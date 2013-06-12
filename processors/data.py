import math
import logging
import numpy as np
import cv2

from track_list import TrackList
from target import Target

AREA_THRESHOLD = 50
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075
POS_THRESHOLD = 0.05


class DataProcessor(object):
    def __init__(self):
        self.targets = []
        self.coverages = {}
        self.track_list = TrackList()

    def process(self, data, img_proc):
        # Only process if calibrated
        if not img_proc.cal_data:
            return

        for contour in data:
            area = cv2.contourArea(contour)
            if area > AREA_THRESHOLD:
                center, radius = cv2.minEnclosingCircle(contour)

                # Translate to origin
                #center = [center[0] - (img_proc.img_source.width / 2), 
                          #img_proc.img_source.height - center[1]]

                ## Convert to polar and subtract radius
                #r = math.sqrt(center[0]**2 + center[1]**2) - (radius)
                #if center[0] == 0:
                    #center[0] = 0.00001
                #theta = math.atan(center[1] / center[0])

                ## Convert back to cartesian and translate
                #center = [r * math.cos(theta), r * math.sin(theta)]
                #center[0] = center[0] + (img_proc.img_source.width / 2)
                #center[1] = img_proc.img_source.height - center[1]

                pos = convertToGlobal(img_proc, center)
                logging.debug("Target Detection: %s" % pos)

                self.track_list.processDetection(pos)
                # TODO Clean reference up
                self.targets = self.track_list.tracks

    def clearTargetData(self):
        self.track_list.tracks = []
        self.targets = []

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
    
    return np.array( np.linalg.inv(rotation) * ( s * np.linalg.inv(intrinsic) * imgPoint - translation ) )
