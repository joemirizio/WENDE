import cv2 as cv
import numpy as np
import os
import logging
from math import sin, cos, pi

# CONSTANTS
SCALE = 1 # Scaling factor for global coordinates wrt feet, ex. 12 makes units inches, 1 makes unit feet
SIDE_ANGLE = pi/3
DISTANCES = (5, 10, 12)

# Calibration point position calculations
DISTANCES = [distance * SCALE for distance in DISTANCES]
SIDE_POINTS = [sin(SIDE_ANGLE), cos(SIDE_ANGLE), 0]
CENTER_POINTS = [0, 1, 0]

RIGHT_POINTS = [[ distance * coordinate for coordinate in SIDE_POINTS] for distance in DISTANCES]
CENTER_POINTS = [[ distance * coordinate for coordinate in CENTER_POINTS] for distance in DISTANCES]
LEFT_POINTS = [[ -1 * x, y, z ] for x, y, z in RIGHT_POINTS ]


class SourceCalibrationModule(object):

    def __init__(self, image_processor, config):
        self.image_processor = image_processor
        self.config = config
        
        center_thresh_min = np.array(config.get('calibration', 'center_color_min').split(','), np.uint8)
        center_thresh_max = np.array(config.get('calibration', 'center_color_max').split(','), np.uint8)
        side_thresh_min = np.array(config.get('calibration', 'side_color_min').split(','), np.uint8)
        side_thresh_max = np.array(config.get('calibration', 'side_color_max').split(','), np.uint8)

        self.colors = [(center_thresh_min, center_thresh_max), 
                        (side_thresh_min, side_thresh_max)]

    def calibrate(self, cal_points=None):
        """ Calibrates the image processor
        
        """
        # Send status update to tactical display to begin calibration
        #self.image_processor.tca.tactical.updateCalibration(1)
        
        self.image_processor.cal_data = CalibrationData()

        # Intrinsic
        self.loadIntrinsicParams()
        self.calcDistortionMaps()

        # Extrinsic
        if not cal_points:
            cal_points = self.getCalibrationPoints()
        self.calcExtrinsicParams(cal_points)

        # Send status update to tactical display that calibration is complete
        #self.image_processor.tca.tactical.updateCalibration(2)

    def getCalibration(self):
        """ Returns calibration data from image processors
            
        """
        
        return self.image_processor.cal_data
   
    def getCalibrationPoints(self):
        # Capture Image
        frame = self.image_processor.img_source.read()
        avg_frame = frame
        height, width = frame.shape[:2]
        
        # Find centers of calibration points
        cal_points = []
        for color in self.colors:
            # Get Contours
            _, _, contours = self.image_processor.odm.findObjects(
                                frame, avg_frame,
                                self.image_processor.frame_type, 
                                color[0], color[1])
            
            # Get center points
            for contour in contours:
                center, radius = cv.minEnclosingCircle(contour)
                if radius > 10:
                    cal_points.append(center)

        return cal_points

    def calcExtrinsicParams(self, cal_points): 
        """ Collects images and calculates extrinsic parameters, storing them in ImageProcessor object
        
        Arguments: 
            cal_points -- The calibration points
    
        """
        # Verify image points are valid
        if not len(cal_points) == 6:
            logging.error("Given " + str(len(cal_points)) + " calibration points. (Expected 6): %s" % cal_points)
            self.image_processor.cal_data = None
            return

        # Create array from detected points
        imagePoints = np.array( cal_points, np.float32 )
        
        # Determine whether left or right view and create appropriate object points array
        if cal_points[0][0] < cal_points[5][0]: # Right Camera (center points farther left than side points)
            objectPoints = np.array( (CENTER_POINTS + RIGHT_POINTS), np.float32 )
        else:
            objectPoints = np.array( (CENTER_POINTS + LEFT_POINTS), np.float32 )
        
        # Calculate extrinsic parameters
        logging.debug("-------------------------------")
        logging.debug("objectPoints: %s" % objectPoints)
        logging.debug("imagePoint: %s" % imagePoints)
        logging.debug("intrinsic: %s" % self.image_processor.cal_data.intrinsic)
        logging.debug("distortion: %s" % self.image_processor.cal_data.distortion)
        _, rvec, tvec = cv.solvePnP(objectPoints, imagePoints, self.image_processor.cal_data.intrinsic, self.image_processor.cal_data.distortion)
        rotation , _= cv.Rodrigues(rvec)
        translation = tvec
        
        # Store in camera object
        self.image_processor.cal_data.rotation = rotation
        self.image_processor.cal_data.translation = translation
        self.image_processor.cal_data.object_points = objectPoints
        self.image_processor.cal_data.image_points = imagePoints

    def loadIntrinsicParams(self):
        """ Loads intrinsic matrix and distortion coefficients from xml files into ImageProcessor object, and calculates distortion map
        
        """

        ### TODO Possibly add files to config
        self.image_processor.cal_data.intrinsic = np.loadtxt(
            os.path.join('processors', 'calibration_data', 'intrinsics.txt'))
        self.image_processor.cal_data.distortion = np.loadtxt(
            os.path.join('processors', 'calibration_data', 'distortion.txt'))
        
        
    def calcDistortionMaps(self):
        """ Calculates distortion maps 
            
        """
        
        cal_data = self.image_processor.cal_data
        size = (self.image_processor.img_source.height, 
                self.image_processor.img_source.width)
        
        # Calculate newCameraMatrix
        camera_matrix, _ = cv.getOptimalNewCameraMatrix(
            cal_data.intrinsic, cal_data.distortion, size, 0.0)
        
        # Calculate Distortion Maps
        cal_data.map1, cal_data.map2 = cv.initUndistortRectifyMap(
            cal_data.intrinsic, cal_data.distortion, 
            None, camera_matrix, size, cv.CV_32FC1)


class CalibrationData(object):
    
    def __init__(self):
        self.intrinsic = None
        self.distortion = None
        self.map1 = None
        self.map2 = None
        self.rotation = None
        self.translation = None
        self.image_points = None
        self.object_points = None

    def __eq__(self):
        return self.rotation and self.translation and self.image_points
