import cv2 as cv
import numpy as np
import time
import datetime

DEFAULT_OUTPUT_DIR = "../"
DEFAULT_IMG_EXT = "png"

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

	def save(self, filename=""):
		if not filename:
			time_stamp = datetime.datetime.fromtimestamp(
					time.time()).strftime('%Y-%m-%d_%H-%M-%S')
			filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp, 
						".", DEFAULT_IMG_EXT])
		cv.imwrite(filename, self.read())


def getCapture(cap_index):
	return cv.VideoCapture(cap_index)
