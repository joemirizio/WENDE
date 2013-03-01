class HighGUI:
	def __init__(self, name, cameras={}):
		self.name = name
		for camera in cameras:
			self.addCamera(camera)

	def start(self, init_func):
		init_func()
	
	def update(self, update_func):
		update_func()

	def addCamera(self, camera):
		cv.namedWindow(self.name + camera.name, cv.CV_WINDOW_AUTOSIZE)

	def updateCamera(self, name, frame):
		cv.imshow(self.name + name, frame)
