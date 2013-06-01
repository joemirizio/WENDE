import cv2 as cv
import numpy as np
import itertools as it
import logging
from math import sin, cos, pi

FLANN_INDEX_KDTREE = 1
FLANN_INDEX_LSH = 6

SCALE = 12 # Scaling factor for global coordinates wrt feet, ex. 12 makes units inches, 1 makes unit feet
DISTS = (6, 10, 12)

# Constant values for calibration points with zero offset
LEFT_PTS = [[dist * SCALE * x for x in (-1 * cos(pi/3), sin(pi/3))] for dist in DISTS]
CENTER_PTS = [
	[0, 6],
	[0, 10],
	[0, 12]
	]
RIGHT_PTS = [[dist * scale * x for x in (cos(pi/3), sin(pi/3))] for dist in DISTS]

class Calibrator(object):

	def __init__(self, image_processors=None):
		self.calibrations = {}
		self.leftPts = []
		self.centerPts = []
		self.rightPts = []
		if image_processors:
			self.calibrateImageProcessors(image_processors)

	def calibrateImageProcessors(self, image_processors):
		for img_proc1, img_proc2 in it.combinations(image_processors, 2):
			self.calibrations[(img_proc1, img_proc2)] = calibrateImages(img_proc1, img_proc2)
		logging.info(repr(self.calibrations))

	def getCalibration(self, img_proc1, img_proc2=None):
		if not img_proc2:
			return [proc_comb for proc_comb in self.calibrations.iteritems() 
					if img_proc1 in proc_comb[0]]
		else:
			return [proc_comb[1] for proc_comb in self.calibrations.iteritems() 
					if img_proc1 in proc_comb[0] and img_proc2 in proc_comb[0]][0]


def calibrateImages(img1, img2):
	flann_params = dict(algorithm=FLANN_INDEX_LSH,
	                   table_number=6, # 12
	                   key_size=12,     # 20
	                   multi_probe_level=1) #2
	image1 = img1.img_source.read();
	image2 = img2.img_source.read();
	gimage1 = cv.cvtColor(image1, cv.COLOR_BGR2GRAY);
	gimage2 = cv.cvtColor(image2, cv.COLOR_BGR2GRAY);
	surfer = cv.SURF(400);
	key_points1 = surfer.detect(gimage1);
	surfer_descriptor = cv.DescriptorExtractor_create("SURF");
	descripters1 = surfer_descriptor.compute(image1,key_points1);
	key_points2 = surfer.detect(image2); 
	descripters2 = surfer_descriptor.compute(image2,key_points2);
	flann_matcher = cv.FlannBasedMatcher(dict(algorithm = FLANN_INDEX_KDTREE,
                    trees = 4),{});
	matches = flann_matcher.match(descripters1[1],descripters2[1]);
	good_matches = [];
	min_dist = matches[1].distance;
	for match in matches:
		if match.distance < min_dist:
			min_dist = match.distance
	for match in matches:
		if match.distance <= 2*min_dist:
			good_matches.append(match)
	i = 0;
	average_dist = 0;
	width, heigth,depth = image1.shape
	dists = [];	
	for match in good_matches:
		i +=1;
		x1, y1 = key_points1[match.queryIdx].pt
		x2, y1 = key_points2[match.trainIdx].pt
		average_dist += (width - x1) + x2;
		dists.append((width - x1) + x2)
		
	average_dist /= i;
	#logging.debug("Distances: %r" % dists)
	offset = 1;
	return average_dist 
	
flann_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=4)

def match_flann(desc1, desc2, r_threshold=0.6):
    flann = cv.flann_Index(desc2, flann_params)
    idx2, dist = flann.knnSearch(desc1, 2, params={})
    mask = dist[:,0] / dist[:,1] < r_threshold
    idx1 = np.arange(len(desc1))
    pairs = np.int32( zip(idx1, idx2[:,0]) )
    return pairs[mask]
   
   
def loadIntrinsicParams(camera):
	""" Loads intrinsic matrix and distortion coefficients from xml files into camera object, and calculates distortion map
	
	Arguments:
		camera -- Camera object
	
	"""

	camera.intrinsic = cv.Load("Intrinsics.xml")
	camera.distortion = cv.Load("Distortion.xml")
	
	
def calcDistortionMaps(camera):
	""" Calculates distortion maps 
	
	Arguments:
		camera -- Camera object
		
	"""
	
	size = camera.height, camera.width
	
	# Calculate newCameraMatrix
	newCameraMatrix, newExtents = cv.getOptimalNewCameraMatrix(camera.intrinsic, camera.distortion, size, 0.0)
	
	# Calculate Distortion Maps
	camera.map1, camera.map2 = cv.initUndistortRectifyMap(camera.intrinsic, camera.distortion, None, newCameraMatrix, size, cv.CV_32FC1)


### TODO -- Implement object detection from images to get imgPoints
def getExtrinsicParams(camera, xOffset, yOffset): 
	""" Collects images and calculates extrinsic parameters, storing them in camera object
	
	Arguments: 
		camera -- Camera object
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
	
	if camera.position == left:
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
	cv2.calibrateCamera(objectPoints, imagePoints, camera.intrinsic, camera.distortion, rvec, tvec)
	cv2.Rodriguez(rvec,rotation)
	translation = tvec
	
	# Store in camera object
	camera.rotation = rotation
	camera.translation = translation
	
	
def undistortImage(camera, image):
	""" Removes distortion from image by applying intrinsic matrix and distortion coefficients
	
	Note: Camera must have intrinsic parameters already loaded
	Arguments:
		camera -- Camera object
		image -- Input image (distorted)
		
	Returns undistorted image
	
	"""
	
	return cv.remap(image, camera.map1, camera.map2, cv.INTER_LINEAR)


def convertToGlobal(camera, input):
	""" Converts x and y coordinates to global coordinates, according to calibration parameters
	
	Arguments:
		camera -- Camera object
		input -- x and y coordinates of input point in a list
		
	Returns a 3D point in with coordinates in an array

	"""
	
	imgPoint = np.array( input.reshape(2, 1), np.float32 )
	leftMat = np.linalg.inv(camera.rotation) * np.linalg.inv(camera.intrinsic) * imgPoint
	rightMat = np.linalg.inv(camera.rotation) * camera.translation
	s = rightMat[2,0]
	s /= leftMat[2,0]
	
	return np.linalg.inv(camera.rotation) * ( s * np.linalg.inv(camera.intrinsic) * imgPoint - translation )
