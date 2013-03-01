import cv2 as cv
from Tkinter import *
from PIL import Image
from PIL import ImageTk

class Tkinter:
	def __init__(self, name, cameras={}):
		self.root = Tk()
		self.root.title(name)
		self.labels = {}

		pos = {'x':0, 'y':0}
		for camera in cameras:
			self.addCamera(camera, pos)
			pos['x'] += camera.width

		# Fullscreen
		w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
		self.root.geometry("%dx%d+0+0" % (w, h))
		self.root.wm_state('zoomed')
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

	def addCamera(self, camera, pos={'x':0, 'y':0}):
		label = Label(self.root)
		label.place(**pos)
		self.labels[camera.name] = label

	def updateCamera(self, name, frame):
		img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		pil_img = Image.fromarray(img)
		photo = ImageTk.PhotoImage(pil_img)
		self.labels[name]['image'] = photo
		self.labels[name].photo = photo


