import cv2 as cv
import Tkinter as tk
from PIL import Image
from PIL import ImageTk

class Tkinter:
	def __init__(self, name, image_processors={}):
		self.root = tk.Tk()
		self.root.title(name)
		self.labels = {}
		self.key_events = {}

		pos = {'x':0, 'y':0}
		for img_proc in image_processors:
			self.addView(img_proc.img_source.name, pos)
			pos['x'] += img_proc.img_source.width

		# Fullscreen
		w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
		self.root.geometry("%dx%d+0+0" % (w, h))
		#self.root.wm_state('zoomed')
		#self.root.overrideredirect(True)
		self.root.attributes('-topmost', True)

		self.root.focus_set()

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

	def addView(self, name, pos={'x':0, 'y':0}):
		label = tk.Label(self.root)
		label.place(**pos)
		self.labels[name] = label

	def updateView(self, name, frame):
		# Check frame dimensions if Gray or BGR and convert to RGB
		if len(frame.shape) == 2:
			img = cv.cvtColor(frame, cv.COLOR_GRAY2RGB)
		else:
			img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		# Convert to PIL
		pil_img = Image.fromarray(img)
		photo = ImageTk.PhotoImage(pil_img)
		# Set PIL to label's image
		self.labels[name]['image'] = photo
		self.labels[name].photo = photo
