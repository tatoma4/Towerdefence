import xml.etree.ElementTree as ET

def convert(value):
	try:
		return int(value)
	except ValueError:
		return float(value)

class ConfigReader:

	def parse_enemies(root):
		'''
		Parse enemy related data from config file
		'''
		enemies = {}
		settings = {}

		for enemy in root.find('EnemyData'):
			for setting in enemy:
				settings.update({setting.tag: setting.text})
			enemies[enemy.tag] = settings
			settings = {}
		return enemies

	def parse_upgrades(upgrade_setting):
		'''
		Parse upgrade related data from config file
		'''
		upgrades = {}
		settings = {}

		for upgrade in upgrade_setting:
			if upgrade.tag == 'MAX_UPGRADE':
				settings.update({upgrade.tag: int(upgrade.text)})
			else:
				converted_tuple = tuple([convert(x) for x in upgrade.text.split(',')])
				settings.update({(upgrade.tag, int(upgrade.attrib['level'])): converted_tuple})
		return settings

	def parse_towers(root):
		'''
		Parse tower related data from config file
		'''
		towers = {}
		settings = {}

		for tower in root.find('TowerData'):
			for setting in tower:
				if setting.tag == 'Upgrades':
					settings.update({setting.tag: ConfigReader.parse_upgrades(setting)})
				else:
					settings.update({setting.tag: setting.text})
				#Add parsing for updates later on here
			towers[tower.tag] = settings
			settings = {}
		#print(towers)
		return towers

	def parse_config(filename):
		configs = {}
		try:
			root = ET.parse(filename).getroot()
			configs["EnemyData"] = ConfigReader.parse_enemies(root)
			configs["TowerData"] = ConfigReader.parse_towers(root)
		except ET.ParseError:
			print("Corrupted config file!")
			return False
		return configs