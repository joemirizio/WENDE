import logging
import Tkinter as tk

class TacticalDisplay(object):
	
	PADDING = 5
	WIDTH = 800
	HEIGHT = 600
	SIZE = (WIDTH, HEIGHT)
	MAX_LEN = 12

	def __init__(self, display, data_proc):
		self.display = display
		self.data_proc = data_proc
		self.tracks = {}
		self.canvas = tk.Canvas(self.display, bg="blue",
				width=TacticalDisplay.WIDTH + TacticalDisplay.PADDING, 
				height=TacticalDisplay.HEIGHT + TacticalDisplay.PADDING)
		self.canvas.grid()

		self.drawBackground()

	def displayTarget(self, target):
		if target not in self.tracks:
			#logging.info("displayTarget: %s" % target)
			points = self.getBoundingBox(0.2, target.pos)
			icon = self.canvas.create_oval(points, fill="black")
			self.tracks[target] = icon
		else:
			points = self.getBoundingBox(0.2, target.pos)
			self.canvas.coords(self.tracks[target], *points)

	def update(self):
		for target in self.data_proc.targets:
			self.displayTarget(target)

	def getBoundingBox(self, length, pos=[WIDTH / 2, HEIGHT / 2]):
		max_len = TacticalDisplay.MAX_LEN
		pad = TacticalDisplay.PADDING
		l = max_len - ((max_len - length) / 2.0)
		offset = ((TacticalDisplay.WIDTH / max_len) * 
				(max_len * (l / max_len)))
		# points = [topLeftx, topLefty, bottomRx, bottomRy]
		points = ([TacticalDisplay.WIDTH - offset + pad] * 2 + 
				[offset + pad] * 2)

		# Offset from top, left
		w_offset = TacticalDisplay.WIDTH / 2.0 - pos[0]
		h_offset = TacticalDisplay.HEIGHT / 2.0 - pos[1]
		points[0] -= w_offset; points[2] -= w_offset
		points[1] -= h_offset; points[3] -= h_offset

		return points

	def drawBackground(self):
		start_angle = 30
		sweep_angle = 120

		pred_points = self.getBoundingBox(12.0)
		alrt_points = self.getBoundingBox(10.0)
		safe_points = self.getBoundingBox(5.0)

		# Currently set so the point of wedge at 250
		pred_zone = self.canvas.create_arc(pred_points, start=start_angle, extent=sweep_angle, fill="yellow", width=0, outline="")
		alrt_zone = self.canvas.create_arc(alrt_points, start=start_angle, extent=sweep_angle, fill="red", width=0, outline="")
		safe_zone = self.canvas.create_arc(safe_points, start=start_angle, extent=sweep_angle, fill="green", width=0, outline="")
