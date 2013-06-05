import cv2 as cv
import numpy as np
import itertools as it
import logging
from math import sin, cos, pi
from image import ImageProcessor
from image import findObjects
from processors.CalibrationData import CalibrationData

# CONSTANTS
SCALE = 1 # Scaling factor for global coordinates wrt feet, ex. 12 makes units inches, 1 makes unit feet
SIDE_ANGLE = pi/3
DISTANCES = (5, 10, 12)

# CALIBRATION POINT COLORS
CENTER_THRESH_MIN = [8, 165, 105]
CENTER_THRESH_MAX = [19, 203, 169]
SIDE_THRESH_MIN = [79, 49, 26]
SIDE_THRESH_MAX = [130, 86, 240]

# Calibration point position calculations
DISTANCES = [distance * SCALE for distance in DISTANCES]
SIDE_POINTS = [sin(SIDE_ANGLE), cos(SIDE_ANGLE), 0]
CENTER_POINTS = [0, 1, 0]

RIGHT_POINTS = [[ distance * coordinate for coordinate in SIDE_POINTS] for distance in DISTANCES]
CENTER_POINTS = [[ distance * coordinate for coordinate in CENTER_POINTS] for distance in DISTANCES]
LEFT_POINTS = [[ -1 * x, y, z ] for x, y, z in RIGHT_POINTS ]

# Detection Colors
center_thresh_min = np.array(CENTER_THRESH_MIN, np.uint8)
center_thresh_max = np.array(CENTER_THRESH_MAX, np.uint8)
side_thresh_min = np.array(SIDE_THRESH_MIN, np.uint8);
side_thresh_max = np.array(SIDE_THRESH_MAX, np.uint8);

colors = [(center_thresh_min, center_thresh_max), 
          (side_thresh_min, side_thresh_max)]


class Calibrator(object):

    def __init__(self, image_processors=None):
        
        if image_processors:
            self.calibrateImageProcessors(image_processors)


    def calibrateImageProcessors(self, image_processors):
        """ Calibrates input ImageProcessors
        
        Arguments:
            image_processors -- Image Processor objects
            
        """
        
        for imageProc in image_processors:
            imageProc.cal_data = CalibrationData()
            # Intrinsic
            imageProc.loadIntrinsicParams()
            imageProc.calcDistortionMaps()

            # Extrinsic
            self.calcExtrinsicParams(imageProc)
            

    def getCalibration(self, img_proc1, img_proc2=None):
        """ Returns calibration data from image processors
        
        Arguments:
            img_proc1 -- ImageProcessor object
            img_proc2 -- (Optional) ImageProcessor object
            
        """
        
        if not img_proc2:
            return img_proc1.cal_data
        else:
            return (img_proc1.cal_data, img_proc2.cal_data)
   
    ### TODO -- Implement object detection from images to get imgPoints
    def calcExtrinsicParams(self, imageProc): 
        """ Collects images and calculates extrinsic parameters, storing them in ImageProcessor object
        
        Arguments: 
            imageProc -- ImageProcessor object
    
        """
           
        # Capture Image
        frame = imageProc.img_source.read()
        avg_frame = frame
        height, width = frame.shape[:2]
        
        # Find centers of calibration points
        calCenters = []
        for i, color in enumerate(colors): ### TODO : IMPLEMENT SUCH THAT WE FILTER DIFFERENT COLORS FOR CENTER/SIDE
            # Get Contours
            _, _, contours = findObjects(frame, avg_frame,
                                imageProc.frame_type, 
                                color[0], color[1])
            
            # Get center points (Should get three, TODO : ADD EXCEPTION AND RETRY IF DIFFERENT)
            for contour in contours:
                center, radius = cv.minEnclosingCircle(contour)
                if radius > 10:
                    calCenters.append(center)

        # Log and error check
        logging.debug("Centers: %s" % calCenters)
        if not len(calCenters) == 6:
            logging.error("All calibration points not found (Need 6): %s" %
                          calCenters)
            imageProc.cal_data = None
            return
        
        # Create array from detected points
        imagePoints = np.array( calCenters, np.float32 )
        
        # Determine whether left or right view and create appropriate object points array
        if calCenters[0][0] < calCenters[5][0]: # Right Camera (center points farther left than side points)
            objectPoints = np.array( (CENTER_POINTS + RIGHT_POINTS), np.float32 )
        else:
            objectPoints = np.array( (CENTER_POINTS + LEFT_POINTS), np.float32 )
        
        # Calculate extrinsic parameters
        logging.debug("-------------------------------")
        logging.debug("objectPoints: %s" % objectPoints)
        logging.debug("imagePoint: %s" % imagePoints)
        logging.debug("intrinsic: %s" % imageProc.cal_data.intrinsic)
        logging.debug("distortion: %s" % imageProc.cal_data.distortion)
        _, rvec, tvec = cv.solvePnP(objectPoints, imagePoints, imageProc.cal_data.intrinsic, imageProc.cal_data.distortion)
        rotation , _= cv.Rodrigues(rvec)
        translation = tvec
        
        # Store in camera object
        imageProc.cal_data.rotation = rotation
        imageProc.cal_data.translation = translation
