import logging

class TacticalDisplay(object):
	
	def __init__(self, gui):
		self.gui = gui
		self.targets = {}

	def addTarget(self, target):
		self.targets[target.name] = target

	def displayTarget(self, target):
		logging.info("displayTarget: %s @ %s" % (target.name, target.pos))
		#TODO Add display logic here	

	def update(self):
		for target in self.targets:
			self.displayTarget(target)
