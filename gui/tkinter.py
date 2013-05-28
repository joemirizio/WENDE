import cv2 as cv
from Tkinter import *
from PIL import Image
from PIL import ImageTk

class Tkinter:
	def __init__(self, name, image_processors={}):
		self.root = Tk()
		self.root.title(name)
		self.labels = {}

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

	def start(self, init_func):
		self.root.after(0, init_func)
		self.root.mainloop()
	
	def update(self, update_func):
		self.root.update()
		self.root.after(0, update_func)

	def addView(self, name, pos={'x':0, 'y':0}):
                #label the target with its x and y coordinates
		label = Label(self.root)
		label.place(**pos)
		self.labels[name] = label

	def updateView(self, name, frame):
                #set view with color scheme, grab images
		img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		pil_img = Image.fromarray(img)
		photo = ImageTk.PhotoImage(pil_img)
		self.labels[name]['image'] = photo
		self.labels[name].photo = photo
