import logging
import Tkinter as tk

class TacticalDisplay(object):
	
	def __init__(self, display, data_proc):
		self.display = display
		self.data_proc = data_proc
		self.canvas = tk.Canvas(self.display, bg="blue", height=250, width=300)
		self.canvas.pack()

	def displayTarget(self, target):
		logging.info("displayTarget: %s" % target)
		#TODO Add display logic here - dots that follow the target - tracer	

	def update(self):
		# Initialize - background things
		coord = [10, 50, 240, 210]
		self.canvas.create_arc(coord, start=0, extent=150, fill="red")

		for target in self.data_proc.targets:
			self.displayTarget(target)
