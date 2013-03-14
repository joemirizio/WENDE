import cv2 as cv
import Tkinter as tk
import tkSimpleDialog
import numpy as np
from PIL import Image
from PIL import ImageTk
import logging

from display.tactical import TacticalDisplay

DEFAULT_VIEWPORT_SIZE = (400, 300)
VIEWPORT_PADDING = 10

class Tkinter(object):
	def __init__(self, name, image_processors={}):
		self.root = tk.Tk()
		self.root.title(name)
		self.viewports = {}
		self.key_events = {}

		# Fullscreen
		w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
		self.root.geometry("%dx%d+0+0" % (w, h))
		#self.root.wm_state('zoomed')
		#self.root.overrideredirect(True)
		self.root.attributes('-topmost', True)
		self.root.focus_set()

		# Main frame
		self.frame = tk.Frame(self.root)
		self.frame.grid(columnspan=2, rowspan=2, sticky=(tk.N, tk.S))

		# Tactical frame
		self.tactical_frame = tk.Frame(self.frame, 
				width=TacticalDisplay.WIDTH, 
				height=TacticalDisplay.HEIGHT)
		self.tactical_frame.grid(column=1, row=0, rowspan=2)

		size = DEFAULT_VIEWPORT_SIZE
		#pos = {'x':0, 'y':0}
		pos = [0, 0]
		for img_proc in image_processors:
			self.addView(img_proc.img_source.name, pos, size)
			#pos['x'] += size[0] + VIEWPORT_PADDING
			pos[1] = pos[1] + 1

		self.root.bind("<Escape>", lambda e: e.widget.quit())

	def addKeyEvent(self, key, event):
		if key in self.key_events:
			raise Exception("Callback already registered to %s" % key)
		self.key_events[key] = event

	def keyPress(self, event):
		for key, callback in self.key_events.iteritems():
			if event.char == key:
				callback()

	def start(self, init_func):
		self.root.bind("<Key>", self.keyPress)
		self.root.after(0, init_func)
		self.root.mainloop()
	
	def update(self, update_func):
		self.root.update()
		self.root.after(0, update_func)

	def addView(self, name, pos={'x':0, 'y':0}, size=(0, 0)):
		label = tk.Label(self.frame)
		if 'x' in pos:
			label.place(**pos)
		else:
			label.grid(column=pos[0], row=pos[1])
		self.viewports[name] = Viewport(name, label, pos, size)
		self.viewports[name].view.bind('<Button-1>', lambda e: self.viewports[name].addPerspectivePoint([e.x, e.y]))
		self.viewports[name].view.bind('<Button-2>', lambda e: self.viewports[name].clearPerspectivePoints())

	def updateView(self, name, frame):
		viewport = self.viewports[name]
		frame = cv.resize(frame, viewport.size)
		# Check frame dimensions if Gray or BGR and convert to RGB
		if len(frame.shape) == 2:
			img = cv.cvtColor(frame, cv.COLOR_GRAY2RGB)
		else:
			img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		
		if len(viewport.quad_points) > 1:
			cv.fillPoly(img, np.array([viewport.quad_points], np.int32), (0, 0, 255))
		if viewport.perspective is not None:
			img = cv.warpPerspective(img, viewport.perspective, img.shape[0:2][::-1])

		# Convert to PIL
		pil_img = Image.fromarray(img)
		photo = ImageTk.PhotoImage(pil_img)
		# Set PIL to label's image
		viewport.view['image'] = photo
		viewport.view.photo = photo

class Viewport(object):
	def __init__(self, name, view, pos={'x':0, 'y':0}, size=[0, 0]):
		self.name = name
		self.view = view
		self.pos = pos
		self.size = size
		self.quad_points = []
		self.perspective = None
		self.full_perspective = [
				[0, 0], [self.size[0], 0], 
				self.size, [0, self.size[1]]]
	
	def addPerspectivePoint(self, point):
		self.quad_points.append(point)
		if len(self.quad_points) == 4:
			self.perspective = cv.getPerspectiveTransform(
					np.array(self.quad_points, np.float32), 
					np.array(self.full_perspective, np.float32))
			self.quad_points = []

	def clearPerspectivePoints(self):
		self.quad_points = []
		self.perspective = None


class InputDialog(tkSimpleDialog.Dialog):

	def __init__(self, parent, title=None, labels=['Value']):
		self.labels = labels
		self.data = {}
		tkSimpleDialog.Dialog.__init__(self, parent, title)

	def body(self, root):
		for i, label in enumerate(self.labels):
			tk.Label(root, text=label).grid(row=i)
			val = tk.Entry(root)
			val.grid(row=i, column=1)
			self.data[label] = val

		return self.data[self.labels[0]]

	def apply(self):
		result = {}
		for label, val in self.data.iteritems():
			result[label] = val.get()
		self.result = result
