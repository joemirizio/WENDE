import cv2 as cv
import Tkinter as tk
import numpy as np
from PIL import Image
from PIL import ImageTk

DEFAULT_VIEWPORT_SIZE = (400, 300)
VIEWPORT_PADDING = 10
TACTICAL_SIZE = (500, 500)

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
		self.tactical_frame = tk.Frame(self.frame, width=TACTICAL_SIZE[0], height=TACTICAL_SIZE[1])
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

	def updateView(self, name, frame):
		viewport = self.viewports[name]
		frame = cv.resize(frame, viewport.size)
		# Check frame dimensions if Gray or BGR and convert to RGB
		if len(frame.shape) == 2:
			img = cv.cvtColor(frame, cv.COLOR_GRAY2RGB)
		else:
			img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		
		if viewport.perspective is not None:
			img = cv.warpPerspective(img, viewport.perspective)

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
				[0, 0], [0, self.size[1]], 
				[self.size[0], 0], [self.size[0], self.size[1]]]
	
	def addPerspectivePoint(self, point):
		self.quad_points.append(point)
		if len(self.quad_points) > 4:
			self.quad_points.pop(0)
			self.perspective = cv.getPerspectiveTransform(np.array(self.quad_points), np.array(self.full_perspective))

	def clearPerspectivePoints(self):
		self.quad_points = []
		self.perspective = None
