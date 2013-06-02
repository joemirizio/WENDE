import cv2 as cv
import numpy as np
import itertools as it
import logging
from math import sin, cos, pi

SCALE = 12 # Scaling factor for global coordinates wrt feet, ex. 12 makes units inches, 1 makes unit feet
DISTS = (6, 10, 12)

# Constant values for calibration points with zero offset
LEFT_PTS = [[dist * SCALE * x for x in (-1 * cos(pi/3), sin(pi/3))] for dist in DISTS]
CENTER_PTS = [
	[0, 6],
	[0, 10],
	[0, 12]
	]
RIGHT_PTS = [[dist * SCALE * x for x in (cos(pi/3), sin(pi/3))] for dist in DISTS]

class Calibrator(object):

	def __init__(self, image_processors=None):
		self.leftPts = []
		self.centerPts = []
		self.rightPts = []
		
		if image_processors:
			self.calibrateImageProcessors(image_processors)

	def calibrateImageProcessors(self, image_processors):
		
		pass

	def getCalibration(self, img_proc1, img_proc2=None):
		""" Returns calibration data from image processors
		
		Arguments:
			img_proc1 -- ImageProcessor object
			img_proc2 -- (Optional) ImageProcessor object
			
		"""
		
		if not img_proc2:
			return img_proc1.calData
		else:
			return (img_proc1.calData, img_proc2.calData)
   

### TODO -- Implement object detection from images to get imgPoints
def calcExtrinsicParams(imageProc, xOffset, yOffset): 
	""" Collects images and calculates extrinsic parameters, storing them in camera object
	
	Arguments: 
		imageProc -- ImageProcessor object
		xOffset -- Distance offset in x direction, specified in inches
		yOffset -- Distance offset in y direction, specified in inches

	"""
	
	# Some local variables...
	objectPoints = []
	imagePoints = []
	
	# Add necessary offset for global coordinate system (there should be no negative numbers...)
	leftPts = [[xOffset + point[0], yOffset + point[1]] for point in LEFT_POINTS]
	centerPts = [[xOffset + point[0], yOffset + point[1]] for point in CENTER_POINTS]
	rightPts = [[xOffset + point[0], yOffset + point[1]] for point in RIGHT_POINTS]
	
	# Append object points to array
	if imageProc.position == left:
		objPtsArray = np.array( (centerPts + leftPts), np.float32 )
	else:
		objPtsArray = np.array( (centerPts + rightPts), np.float32 )
	objectPoints.append(objPtsArray)
	
	# Capture Image
	height, width = image.shape[:2]
	
	# Filter Color 1 (center)
	# Detect calibration points and put into list ([ [x, y], [x, y], [x, y] ])
	# Filter Color 2 (left/right)
	# Detect calibration points and put into list ([ [x, y], [x, y], [x, y] ])
	imgPtsArray = np.array( (imgPtsCenter + imgPtsSide), np.float32 )
	imagePoints.append(imgPtsArray)
	
	# Calculate extrinsic parameters
	cv2.calibrateCamera(objectPoints, imagePoints, imageProc.intrinsic, imageProc.distortion, rvec, tvec)
	cv2.Rodriguez(rvec,rotation)
	translation = tvec
	
	# Store in camera object
	imageProc.rotation = rotation
	imageProc.translation = translation
	
