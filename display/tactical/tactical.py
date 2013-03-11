import logging
import Tkinter

class TacticalDisplay(object):
	
	def __init__(self, display):
		self.display = display
		self.targets = {}

	def addTarget(self, target):
		self.targets[target.name] = target

	def displayTarget(self, target):
		logging.info("displayTarget: %s @ %s" % (target.name, target.pos))
		#TODO Add display logic here - dots that follow the target - tracer	

	def update(self):
                #initialize - background things
                top = Tkinter.Tk()
                C = Tkinter.Canvas(top, bg="blue", height=250, width=300)

                coord = 10, 50, 240, 210
                C.create_arc(coord, start=0, extent=150, fill="red")

                C.pack()
                top.mainloop()
                
		for target in self.targets:
			self.displayTarget(target)

