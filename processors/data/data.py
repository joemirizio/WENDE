import math
import logging
import numpy as np
import cv2

from discrimination import TargetDisciminationModule
from track import TargetTrackModule
from target import Target
from correlation import TargetCorrelationModule

AREA_THRESHOLD = 50
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075
POS_THRESHOLD = 0.05


class DataProcessor(object):
    """
    Top level class for processing position data. Handles prediction,
    correlation, and track.
    
    Args: None
    """
    
    def __init__(self, tca):
        self.targets = []
        self.coverages = {}
        self.tca = tca
        self.config = tca.config
        self.is_active = True
        # Target correlation module
        self.tcm = TargetCorrelationModule(self)
        # Target Discimination Module
        self.tdm = TargetDisciminationModule(self)
        # Target Track Module
        self.ttm = TargetTrackModule(self)

    def process(self):
        """
        Process the next set of calibrated data from the discrimination module.
        
        Args: None
        """
        
        # Only process if active
        if not self.is_active:
            return

        filtered_positions = []
        
        for image_processor in self.tca.image_processors:
            # Only process if calibrated
            if not image_processor.cal_data.is_valid:
                continue

            # Discriminate positions
            self.tdm.discriminate(image_processor.last_detected_positions,
                                  image_processor)

       
#        [[[x1,y1],[x2,y2],[x3,y3]],...]

        unique_positions = self.tcm.checkUnique(self.tca.image_processors)

        logging.debug("-" * 20)
        logging.debug("UNIQUE POSITIONS: %s" % unique_positions)

        self.ttm.processDetections(unique_positions)

        # TODO Clean reference up
        self.targets = self.ttm.targets
        # TODO remove
        for target in self.ttm.targets:
            logging.debug("TARGET: %s" % target)

    def clearTargetData(self):
        """
        Clear all track data from the Target
        track module.
        
        Args: None
        """
        
        del self.ttm.targets[:]
        del self.targets[:]

    def toggleActive(self):
        self.is_active = not self.is_active

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
    
    # Convert to numpy array
    coordinates = np.array(coordinates)

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
