import cv2 as cv
import math
import logging

from target import Target

AREA_THRESHOLD = 200
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075
POS_THRESHOLD = 0.05

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
				y = float(center[1]) / float(img_proc.img_source.height) * img_proc.coverage_size[1] 
				y = img_proc.A + (img_proc.B * y) + (img_proc.C * y**2)
				pos = ([float(center[0]) / float(img_proc.img_source.width) * img_proc.coverage_size[0] - (img_proc.coverage_size[0] / 2) + img_proc.coverage_offset[0],
						img_proc.coverage_size[1] - y + img_proc.coverage_offset[1]])

				self.addTarget(Target(pos))
		self.addCoverage(img_proc)

	def addTarget(self, target):
		isPresent = False
		for tgt in self.targets:
			dist = distance(target.pos, tgt.pos)
			if dist < DETECT_THRESHOLD:
				isPresent = True
				if dist > TRACK_THRESHOLD:
					tgt.recordPosition()
				if dist > POS_THRESHOLD:
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

def undistortImage(imageProc, image):
	""" Removes distortion from image by applying intrinsic matrix and distortion coefficients
	
	Note: ImageProcessor must have intrinsic parameters already loaded
	Arguments:
		imageProc -- ImageProcessor object
		image -- Input image (distorted)
		
	Returns undistorted image
	
	"""
	
	return cv.remap(image, imageProc.map1, imageProc.map2, cv.INTER_LINEAR)


def convertToGlobal(imageProc, input):
	""" Converts x and y coordinates to global coordinates, according to calibration parameters
	
	Arguments:
		imageProc -- ImageProcessor object
		input -- x and y coordinates of input point in a list
		
	Returns a 3D point in with coordinates in an array

	"""
	
	imgPoint = np.array( input.reshape(2, 1), np.float32 )
	leftMat = np.linalg.inv(imageProc.rotation) * np.linalg.inv(imageProc.intrinsic) * imgPoint
	rightMat = np.linalg.inv(imageProc.rotation) * imageProc.translation
	s = rightMat[2,0]
	s /= leftMat[2,0]
	
	return np.linalg.inv(imageProc.rotation) * ( s * np.linalg.inv(imageProc.intrinsic) * imgPoint - imageProc.translation )

