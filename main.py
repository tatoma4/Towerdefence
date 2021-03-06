from PyQt5.QtWidgets import QApplication
import sys

from enemy import *
from gameworld import *
from tower import * 
from mapreader import *
from configreader import *
from gui import GUI

def main():
	world = MapReader.parse_map("default_map.xml")
	if not world:
		sys.exit()
	configs = ConfigReader.parse_config("default_config.xml")
	if not configs:
		sys.exit()
	world.add_config(configs)
	
	app = QApplication(sys.argv)
	gui = GUI(world, 30)

	app.exec_()
	app.deleteLater()
	sys.exit()

if __name__ == '__main__':
	main()