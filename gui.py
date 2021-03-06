from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication
from tower_graphics_item import TowerGraphicsItem
from enemy_graphics_item import EnemyGraphicsItem
from projectile import Projectile
from tower import TowerType, Tower
from functools import partial

class QScene(QtWidgets.QGraphicsScene):
	def __init__(self, gui):
		QtWidgets.QGraphicsScene.__init__(self)
		self.gui = gui
		self.connected = False

	def disconnect_buttons(self):
		if self.connected:
			self.gui.attack_speed_upgrade_btn.clicked.disconnect()
			self.gui.range_upgrade_btn.clicked.disconnect()
			self.gui.damage_upgrade_btn.clicked.disconnect()
			self.connected = False

	def mousePressEvent(self, ev):
		if ev.button() == QtCore.Qt.LeftButton:
			pos = ev.scenePos()
			unit = self.gui.selected_unit
			coord = (int(pos.x() / self.gui.square_size), int(pos.y() / self.gui.square_size))
			
			try:
				square = self.gui.world.squares[coord[0]][coord[1]]
				tower = square.get_tower()

				# select tower
				if tower:

					# disable previous tower buttons
					self.disconnect_buttons()

					self.gui.selected_label.setText("Selected tower")
					self.gui.selection_label.setText("{}: {}".format(str(tower.type).split(".")[-1] ,coord))
					self.gui.selected_tower = tower



					# check if upgrade buttons are not connected and connect them only once
					if not self.connected:
						self.gui.attack_speed_upgrade_btn.clicked.connect(partial(self.gui.selected_tower.upgrade, 'UPGRADE_SPEED'))
						self.gui.range_upgrade_btn.clicked.connect(partial(self.gui.selected_tower.upgrade, 'UPGRADE_RANGE'))
						self.gui.damage_upgrade_btn.clicked.connect(partial(self.gui.selected_tower.upgrade, 'UPGRADE_DMG'))
						self.connected = True

					self.gui.selected_unit = None
					self.gui.upgrade_buttons_enabled(True)
				
				# place new tower
				elif unit:
					self.gui.selected_label.setText("Nothing selected")
					self.gui.selection_label.setText("")
					self.gui.selected_unit = None
					self.gui.selected_tower = None
					self.gui.world.add_tower(unit, coord)

					# reset labels
					self.gui.upgrade_buttons_enabled(False)

					# disconnect buttons while switching targets
					self.disconnect_buttons()

				# click elsewhere on map
				else:
					self.gui.upgrade_buttons_enabled(False)
					self.gui.selected_tower = None
					self.gui.selected_label.setText("Nothing selected")
					self.gui.selection_label.setText("")
					self.disconnect_buttons()
								
			except IndexError:
				print("Click out of screen!")


class GUI(QtWidgets.QMainWindow):
	
	def __init__(self, world, square_size):
		super().__init__()

		self.main_widget = QtWidgets.QWidget()
		self.setCentralWidget(self.main_widget)
		self.main_layout = QtWidgets.QHBoxLayout()
		self.game_widget = QtWidgets.QWidget()
		self.side_widget = QtWidgets.QWidget()
		self.game_layout = QtWidgets.QHBoxLayout()

		self.main_layout.addWidget(self.game_widget)
		self.main_layout.addWidget(self.side_widget)
		self.centralWidget().setLayout(self.main_layout)

		self.info_layout = QtWidgets.QVBoxLayout()

		self.side_widget.setLayout(self.info_layout)
		self.game_widget.setLayout(self.game_layout)

		self.world = world
		self.square_size = square_size
		self.tower_graphics_items = []
		self.enemy_graphics_items = []
		self.projectiles = []
		self.selected_unit = None
		self.selected_tower = None

		self.init_window()
		self.init_info_layout()
		self.add_map_grid_items()
		self.add_tower_graphics_items()
		self.add_enemy_graphics_items()

		self.dt = 1/60*1000
		self.logic_timer = QtCore.QTimer()
		self.logic_timer.timeout.connect(self.update_logic)
		self.logic_timer.start(self.dt)

		self.graphic_timer = QtCore.QTimer()
		self.graphic_timer.timeout.connect(self.update_graphics)
		self.graphic_timer.start(1/60*1000)

	def add_map_grid_items(self):
		'''
		Draw base map grid with tiles
		'''
		width = self.world.get_width()
		height = self.world.get_height()

		for x in range(width):
			for y in range(height):
				grid = QtWidgets.QGraphicsRectItem(x * self.square_size, y * self.square_size, self.square_size, self.square_size)
				square = self.world.get_square((x, y))
				if(square.is_start()):
					grid.setBrush(QtGui.QBrush(QtGui.QColor(20, 150, 0))) #Green
				elif(square.is_route()):
					grid.setBrush(QtGui.QBrush(QtGui.QColor(200, 130, 40))) #Brown
				elif(square.is_tower()):
					grid.setBrush(QtGui.QBrush(QtGui.QColor(90, 40, 0))) #Dark Brown
				else:
					grid.setBrush(QtGui.QBrush(QtGui.QColor(180, 0, 0))) #Red

				self.scene.addItem(grid)

	def add_tower_graphics_items(self):
		missing_towers = self.world.get_towers()[:]
		for item in self.tower_graphics_items:
			if item.tower in missing_towers:
				missing_towers.remove(item.tower)
		for tower in missing_towers:
			tower_graphic = TowerGraphicsItem(tower, self.square_size)
			self.tower_graphics_items.append(tower_graphic)
			self.scene.addItem(tower_graphic)

	def add_enemy_graphics_items(self):
		missing_enemies = self.world.get_enemies()[:]
		for item in self.enemy_graphics_items:
			if item.enemy in missing_enemies:
				missing_enemies.remove(item.enemy)
		for enemy in missing_enemies:
			enemy_graphic = EnemyGraphicsItem(enemy, self.square_size)
			self.enemy_graphics_items.append(enemy_graphic)
			self.scene.addItem(enemy_graphic)

	def create_projectile(self, enemy, tower):
		projectile = Projectile(enemy, tower, self.square_size)
		self.projectiles.append(projectile)
		self.scene.addItem(projectile)

	def remove_dead_graphics(self):
		for enemy_graphic in self.enemy_graphics_items:
			if not enemy_graphic.enemy.is_alive():
				self.scene.removeItem(enemy_graphic)
				self.enemy_graphics_items.remove(enemy_graphic)
		for projectile in self.projectiles:
			if not projectile.is_alive():
				self.scene.removeItem(projectile)
				self.projectiles.remove(projectile)

	def update_graphics(self):
		'''
		Update positions of all graphical elements and remove obsolete one's
		'''
		self.add_tower_graphics_items()
		self.add_enemy_graphics_items()
		self.remove_dead_graphics()
		
		for enemy_graphic in self.enemy_graphics_items:
			enemy_graphic.update()
		for tower_graphic in self.tower_graphics_items:
			tower_graphic.update()
		for projectile in self.projectiles:
			projectile.update(self.dt)

		self.update_labels()

	def next_upgrade(self, upgrade_type):
		upgrade_level = self.selected_tower.upgrade_levels[upgrade_type]
		next_upgrade_value = self.selected_tower.upgrades[(upgrade_type, upgrade_level)][0]
		next_upgrade_cost = self.selected_tower.upgrades[(upgrade_type, upgrade_level)][1]
		return next_upgrade_value, next_upgrade_cost

	def update_labels(self):
		'''
		Update informatic labels
		'''
		self.money_label.setText("Money: {}".format(self.world.money))
		self.health_label.setText("HP: {}".format(self.world.base_hp))
		self.wave_label.setText("Wave: {}/{}".format(self.world.current_wave, self.world.max_waves))
		self.enemies_label.setText("Enemies: {}/{}".format(self.world.get_number_of_enemies(), self.world.get_wave_total()))

		# upgrade labels in upgrade buttons if state change was detected
		if self.attack_speed_upgrade_btn.clicked or self.range_upgrade_btn.clicked or self.damage_upgrade_btn.clicked:
			if self.selected_tower:
				self.upgrade_buttons_enabled(True)
		
	def update_logic(self):
		self.update_enemies()
		self.update_spawner()
		self.update_towers()
		self.check_status()
		
	def update_spawner(self):
		'''
		Update enemy spawner logic
		'''
		if self.world.wave_spawner is not None and not self.world.wave_spawner.complete:
			self.world.wave_spawner.update(self.dt)
		else:
			self.world.wave_spawner = None

	def check_status(self):
		'''
		Checks game end status and shows game over or win message
		'''
		if not self.world.alive:
			game_over_message = QtWidgets.QMessageBox()
			game_over_message.setIcon(QtWidgets.QMessageBox.Critical)
			game_over_message.setWindowTitle("Game status")
			game_over_message.setText("Game Over!")
			game_over_message.setInformativeText("Press Ok to exit")
			ret = game_over_message.exec()

			if ret == QtWidgets.QMessageBox.Ok:
				QApplication.instance().exit(1)

		elif self.world.current_wave == self.world.max_waves and not self.world.get_number_of_enemies() and self.world.base_hp:
			win_message = QtWidgets.QMessageBox()
			win_message.setIcon(QtWidgets.QMessageBox.Information)
			win_message.setWindowTitle("Game status")
			win_message.setText("You win!")
			win_message.setInformativeText("Press Ok to exit")
			ret = win_message.exec()

			if ret == QtWidgets.QMessageBox.Ok:
				QApplication.instance().exit(1)

	def update_towers(self):
		'''
		Update tower logic functions
		'''
		for tower in self.world.get_towers():
			# if it returns enemy, tower has attacked, create projectile
			attacked = tower.update(self.dt)
			if attacked:
				self.create_projectile(tower.target, tower)
				tower.target = None

	def update_enemies(self):
		'''
		Update enemy logic functions
		'''
		self.world.remove_dead_enemies()
		enemies = self.world.get_enemies()
		for enemy in enemies:
			if enemy.is_alive():
				enemy.update(self.dt)

	def place_tower(self, tower_type):
		'''
		Sets spesific tower type as active unit
		'''
		self.selected_label.setText("Placing tower")
		self.selected_unit = Tower(tower_type, self.world.configs['TowerData'])
		self.selection_label.setText("{}".format(tower_type).split(".")[-1])


		self.upgrade_buttons_enabled(False)
		self.selected_tower = None

	def upgrade_buttons_enabled(self, value):

		self.attack_speed_upgrade_btn.setEnabled(value)
		self.range_upgrade_btn.setEnabled(value)
		self.damage_upgrade_btn.setEnabled(value)
		if not value:
			self.attack_speed_upgrade_btn.setText("Attack Speed")
			self.damage_upgrade_btn.setText("Damage")
			self.range_upgrade_btn.setText("Range")
		elif value:
			max_upgrade = self.selected_tower.upgrades['MAX_UPGRADE']
			next_atk_speed = self.next_upgrade('UPGRADE_SPEED')
			self.attack_speed_upgrade_btn.setText("Attack Speed: {:0.1f}+({:0.1f}) {}$ {}/{}".format(self.selected_tower.attack_speed, next_atk_speed[0], next_atk_speed[1], self.selected_tower.upgrade_levels['UPGRADE_SPEED'], max_upgrade))
			next_range = self.next_upgrade('UPGRADE_RANGE')
			self.range_upgrade_btn.setText("Range: {:d}+({:d}) {}$ {}/{}".format(int(self.selected_tower.range), int(next_range[0]), next_range[1], self.selected_tower.upgrade_levels['UPGRADE_RANGE'], max_upgrade))
			next_dmg = self.next_upgrade('UPGRADE_DMG')
			self.damage_upgrade_btn.setText("Damage: {:d}+({:d}) {}$ {}/{}".format(int(self.selected_tower.damage), int(next_dmg[0]), next_dmg[1], self.selected_tower.upgrade_levels['UPGRADE_DMG'], max_upgrade))

	def init_info_layout(self):
		'''
		Setups all labels and buttons in right side control panel
		'''

		self.attack_speed_upgrade_btn = QtWidgets.QPushButton("Attack Speed")
		self.range_upgrade_btn = QtWidgets.QPushButton("Range")
		self.damage_upgrade_btn = QtWidgets.QPushButton("Damage")

		self.upgrade_buttons_enabled(False)

		self.health_label = QtWidgets.QLabel()
		self.money_label = QtWidgets.QLabel()
		self.wave_label = QtWidgets.QLabel()
		self.enemies_label = QtWidgets.QLabel()
		self.selected_label = QtWidgets.QLabel("Selected Tower")
		self.selection_label = QtWidgets.QLabel()

		self.info_layout.addWidget(self.health_label)
		self.info_layout.addWidget(self.money_label)
		self.info_layout.addWidget(self.wave_label)
		self.info_layout.addWidget(self.enemies_label)
		self.info_layout.addSpacerItem(QtWidgets.QSpacerItem(200, 200))
		self.info_layout.addWidget(self.selected_label)
		self.info_layout.addWidget(self.selection_label)
		self.info_layout.addStrut(300)

		self.upgrade_label = QtWidgets.QLabel("Upgrades")
		self.info_layout.addWidget(self.upgrade_label)

		self.info_layout.addWidget(self.attack_speed_upgrade_btn)
		self.info_layout.addWidget(self.range_upgrade_btn)
		self.info_layout.addWidget(self.damage_upgrade_btn)
		self.info_layout.addSpacerItem(QtWidgets.QSpacerItem(20, 20))

		self.wave_btn = QtWidgets.QPushButton("Next Wave")
		self.info_layout.addWidget(self.wave_btn)
		self.wave_btn.clicked.connect(self.world.next_wave)
		self.info_layout.addSpacerItem(QtWidgets.QSpacerItem(20, 20))

		self.tower_label = QtWidgets.QLabel("Towers")
		self.info_layout.addWidget(self.tower_label)
		self.tower_btn = QtWidgets.QPushButton("Electric")
		self.info_layout.addWidget(self.tower_btn)
		self.tower_btn.clicked.connect(partial(self.place_tower, TowerType.ELECTRIC_TOWER))
		self.tower_btn2 = QtWidgets.QPushButton("Laser")
		self.tower_btn2.clicked.connect(partial(self.place_tower, TowerType.LASER_TOWER))
		self.info_layout.addWidget(self.tower_btn2)

	def init_window(self):
		'''
		Setup main window and scene
		'''
		self.setGeometry(1024, 720, 1024, 720)
		self.setWindowTitle('Yet Another Tower Defense')
		self.show()

		self.scene = QScene(self)
		self.scene.setSceneRect(0, 0, 600, 600)

		self.view = QtWidgets.QGraphicsView(self.scene, self)
		self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		self.view.show()

		self.game_layout.addWidget(self.view)
		self.game_layout.addStretch()

		