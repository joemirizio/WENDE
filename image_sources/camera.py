import cv2 as cv
import numpy as np

class Camera:
	def __init__(self, name, cap_index, size):
		self.capture = getCapture(cap_index)
		self.name = name
		self.width = size[0]
		self.height = size[1]
		self.capture.set(3, self.width)
		self.capture.set(4, self.height)

	def read(self, flip=True):
		_, frame = self.capture.read()
		if flip:
			frame = cv.flip(frame, 1)
		#frame = cv.pyrDown(frame)
		return frame


def getCapture(cap_index):
	return cv.VideoCapture(cap_index)
