import os
import cv2 as cv

class ImageFile:
	def __init__(self, filename):
		self.name = os.path.splitext(filename)[0]
		self.image = cv.imread(filename)
		self.height, self.width = self.image.shape[:2]

	def read(self):
		return self.image
