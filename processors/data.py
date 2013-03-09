import cv2 as cv
import logging
import math

import display.tactical.target

AREA_THRESHOLD = 1100
DIST_THRESHOLD = 10

class DataProcessor(object):
	
	def __init__(self):
		self.targets = []		

	def addTarget(self, target):
		isPresent = False
		for tgt in self.targets:
			if dist(target, tgt) < DIST_THRESHOLD:
				isPresent = True
		if not isPresent:
			self.targets.append(target)
			logging.debug(target)

	def process(self, data):
		for contour in data:
			area = cv.contourArea(contour)
			if area > AREA_THRESHOLD:
				center, radius = cv.minEnclosingCircle(contour)
				self.addTarget(center)


def dist(p1, p2):
	return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
