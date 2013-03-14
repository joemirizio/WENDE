import Tkinter as tk
import math
import logging

class TacticalDisplay(object):
	
	PADDING = 5
	WIDTH = 800
	HEIGHT = WIDTH / 2
	SIZE = (WIDTH, HEIGHT)
	MAX_RANGE = 12
	MAX_WIDTH = MAX_RANGE * math.cos(math.radians(30))

	def __init__(self, display, data_proc):
		self.display = display
		self.data_proc = data_proc
		self.tgtTracks = {}
		self.canvas = tk.Canvas(self.display, bg="#FEFEFE",
				width=TacticalDisplay.WIDTH + TacticalDisplay.PADDING, 
				height=TacticalDisplay.HEIGHT + TacticalDisplay.PADDING)
		self.canvas.grid()

		self.drawBackground()

		# Log position
		self.canvas.bind("<Button-1>", lambda e: logging.debug("Canvas (%d, %d)" % (e.x, e.y)))
		# Clear target data
		self.canvas.bind("<Button-2>", lambda e: self.clearTargetData())

	def displayTarget(self, target):
		# Remap target position
		#logging.debug("Mapped pos: (%d, %d)" % (target_pos[0], target_pos[1]))
		target_pos = self.remapPosition(target.pos)
		target_pos_points = self.getBoundingBox(0.3, target_pos)

		# Display target and track
		if target not in self.tgtTracks:
			#logging.info("displayTarget: %s" % target)
			tgtTrack = TargetTrack(target)
			tgtTrack.icon = self.canvas.create_oval(target_pos_points, fill="#AA66CC", outline="#9933CC", width=4)
			self.tgtTracks[target] = tgtTrack
		else:
			# Draw track lines
			tgtTrack = self.tgtTracks[target] 
			if len(tgtTrack.target.tracks) > 2:
				# Remap track positions
				track_pts = tgtTrack.target.tracks
				track_points = []
				for point in track_pts:
					track_points.append(self.remapPosition(point))
				# Flatten and add padding
				track_points = flattenArray(track_points)
				track_points = [coord + TacticalDisplay.PADDING for coord in track_points]

				if not tgtTrack.track:
					tgtTrack.track = self.canvas.create_line(*track_points, fill="#FFBB33", width=2, capstyle="round")
				else:
					self.canvas.coords(tgtTrack.track, *track_points)

			# Draw target icon
			self.canvas.coords(tgtTrack.icon, *target_pos_points)
			self.canvas.tag_raise(tgtTrack.icon)

	def remapPosition(self, pos):
		return [pos[0] / TacticalDisplay.MAX_WIDTH * TacticalDisplay.WIDTH, 
				pos[1] / TacticalDisplay.MAX_RANGE * TacticalDisplay.HEIGHT]

	def update(self):
		for target in self.data_proc.targets:
			self.displayTarget(target)

	def getBoundingBox(self, length, pos=[WIDTH / 2, HEIGHT]):
		max_len = TacticalDisplay.MAX_RANGE
		pad = TacticalDisplay.PADDING

		extent_x = TacticalDisplay.WIDTH * (length / max_len) / 2
		extent_y = TacticalDisplay.HEIGHT * (length / max_len)

		# points = [topLeftx, topLefty, bottomRx, bottomRy]
		points = [-extent_x + pos[0] + pad, -extent_y + pos[1] + pad, 
				extent_x + pos[0] + pad, extent_y + pos[1] + pad]

		return points

	def drawBackground(self):
		start_angle = 30
		sweep_angle = 120

		pred_points = self.getBoundingBox(12.0)
		alrt_points = self.getBoundingBox(10.0)
		safe_points = self.getBoundingBox(5.0)

		# Currently set so the point of wedge at 250
		pred_zone = self.canvas.create_arc(pred_points, start=start_angle, extent=sweep_angle, fill="#33B5E5", outline="#0099CC", width=4)
		alrt_zone = self.canvas.create_arc(alrt_points, start=start_angle, extent=sweep_angle, fill="#FF4444", outline="#CC0000", width=4)
		safe_zone = self.canvas.create_arc(safe_points, start=start_angle, extent=sweep_angle, fill="#99CC00", outline="#669900", width=4)
	
	def clearTargetData(self):
		for tgtTrack in self.tgtTracks.itervalues():
			tgtTrack.removeDisplayObjects(self.canvas)
		self.tgtTracks = {}
		self.data_proc.clearTargetData()
	

class TargetTrack(object):
	def __init__(self, target):
		self.target = target
		self.icon = None
		self.track = None
	
	def removeDisplayObjects(self, canvas):
		canvas.delete(self.icon)
		canvas.delete(self.track)

def flattenArray(arr):
	# Flatten points in array
	return [item for sublist in arr for item in sublist]
