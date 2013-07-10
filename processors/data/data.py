import math
import logging
import numpy as np
import cv2

from discrimination import TargetDisciminationModule
from track import TargetTrackModule
from target import Target
import correlation

AREA_THRESHOLD = 50
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075
POS_THRESHOLD = 0.05


class DataProcessor(object):
    def __init__(self, tca):
        self.targets = []
        self.coverages = {}
        self.tca = tca
        self.config = tca.config
        # Target correlation module
        self.corr = correlation.CorrelationModule(self)
        # Target Discimination Module
        self.tdm = TargetDisciminationModule(self)
        # Target Track Module
        self.ttm = TargetTrackModule(self)

    def process(self, img_processors):
        filtered_positions = []
        
        # Only process if calibrated
        for img_proc in img_processors:
            if not img_proc.cal_data:
                return
            data = img_proc.process()
            filtered_positions.append(self.tdm.discriminate(data, img_proc))
        print filtered_positions
       
#        [[[x1,y1],[x2,y2],[x3,y3]],...]

        unique_positions = self.corr.checkUnique(img_processors,filtered_positions)

        self.ttm.processDetection(unique_positions)

        # TODO Clean reference up
        self.targets = self.ttm.targets

    def clearTargetData(self):
        del self.ttm.targets[:]
        del self.targets[:]

# TODO Possible move 
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
    
    return cv2.remap(image, imageProc.map1, imageProc.map2, cv2.INTER_LINEAR)


def convertToGlobal(imageProc, coordinates):
    """ Converts x and y coordinates to global coordinates, according to calibration parameters
    
    Arguments:
        imageProc -- ImageProcessor object
        coordinates -- x and y coordinates of input point in an array-like object
        
    Returns a 3D point in with coordinates in an array

    """
    
    imgPoint = np.ones( (3, 1), np.float32 )
    imgPoint[0, 0] = coordinates[0]
    imgPoint[1, 0] = coordinates[1]
    
    # Convert to matrix to simplify the following linear algebra
    # TODO: CLEAN THIS UP
    imgPoint = np.matrix(imgPoint)
    intrinsic = np.matrix(imageProc.cal_data.intrinsic)
    rotation = np.matrix(imageProc.cal_data.rotation)
    translation = np.matrix(imageProc.cal_data.translation)
    
    leftMat = np.linalg.inv(rotation) * np.linalg.inv(intrinsic) * imgPoint
    rightMat = np.linalg.inv(rotation) * translation
    s = rightMat[2,0]
    s /= leftMat[2,0]
    
    position = np.array(np.linalg.inv(rotation) * 
        (s * np.linalg.inv(intrinsic) * imgPoint - translation))[:2]

    # Convert from numpy to list
    from display.tactical.tactical import flattenArray
    position = flattenArray(position.tolist())

    return position
