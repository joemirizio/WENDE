import cv2 as cv
import math
import logging

from target import Target

AREA_THRESHOLD = 1100
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075

class DataProcessor(object):
	
	def __init__(self):
		self.targets = []		
		self.coverages = {}

	def process(self, data, img_proc):
		for contour in data:
			area = cv.contourArea(contour)
			if area > AREA_THRESHOLD:
				center, radius = cv.minEnclosingCircle(contour)
				# Compute offset
				pos = ([float(center[0]) / float(img_proc.img_source.width) * img_proc.coverage_size[0] - (img_proc.coverage_size[0] / 2) + img_proc.coverage_offset[0],
						img_proc.coverage_size[1] - float(center[1]) / float(img_proc.img_source.height) * img_proc.coverage_size[1] + img_proc.coverage_offset[1]])

				self.addTarget(Target(pos))
		self.addCoverage(img_proc)

	def addTarget(self, target):
		isPresent = False
		for tgt in self.targets:
			dist = distance(target.pos, tgt.pos)
			if dist < DETECT_THRESHOLD:
				isPresent = True
				#if dist > TRACK_THRESHOLD:
				tgt.recordPosition()
				tgt.pos = target.pos
		if not isPresent:
			#logging.info("Adding target")
			self.targets.append(target)

	def addCoverage(self, img_proc):
		self.coverages[img_proc] = [img_proc.coverage_size, img_proc.coverage_offset]

	def clearTargetData(self):
		self.targets = []


def distance(p1, p2):
	return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
