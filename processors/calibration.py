import cv2 as cv
import numpy as np
import os
import logging
import pickle
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

    def __init__(self, image_processor):
        self.image_processor = image_processor
        self.config = image_processor.config
        
        center_thresh_min = np.array(self.config.get('calibration', 'center_color_min').split(','), np.uint8)
        center_thresh_max = np.array(self.config.get('calibration', 'center_color_max').split(','), np.uint8)
        side_thresh_min = np.array(self.config.get('calibration', 'side_color_min').split(','), np.uint8)
        side_thresh_max = np.array(self.config.get('calibration', 'side_color_max').split(','), np.uint8)

        self.colors = [(center_thresh_min, center_thresh_max), 
                        (side_thresh_min, side_thresh_max)]

        if self.config.getboolean('calibration', 'use_cal_data'):
            self.loadCalibrationData()

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
        frame = self.image_processor.isi.read()
        avg_frame = frame
        height, width = frame.shape[:2]
        
        # Find centers of calibration points
        cal_points = []
        for color in self.colors:
            # Get Contours
            _, contours = self.image_processor.odm.findObjects(
                            frame, self.image_processor.frame_type, 
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
            logging.error("%s Calibration Failed: %d/6 points: %s" %
                          (self.image_processor.isi.name, len(cal_points),
                           cal_points))
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
        intrinsic_file = self.config.get('calibration', 'cal_intrinsic_file')
        distortion_file = self.config.get('calibration', 'cal_distortion_file')
        logging.debug('Loading intrinsic data from %s, %s' % 
                      (intrinsic_file, distortion_file))
        self.image_processor.cal_data.intrinsic = np.loadtxt(intrinsic_file)
        self.image_processor.cal_data.distortion = np.loadtxt(distortion_file)

    def getCalibrationDataFilename(self):
        filename, ext = os.path.splitext(self.config.get("calibration", "cal_data_file"))
        cal_filename = ''.join([filename, self.image_processor.isi.name, ext])
        return cal_filename
        
    def saveCalibrationData(self):
        with open(self.getCalibrationDataFilename(), 'w') as cal_file:
            #pickle.dump(self.image_processor.cal_data, cal_file)
            self.image_processor.cal_data.save(cal_file)

    def loadCalibrationData(self):
        with open(self.getCalibrationDataFilename(), 'r') as cal_file:
            #self.image_processor.cal_data = pickle.load(cal_file)
            self.image_processor.cal_data.load(cal_file)

    def calcDistortionMaps(self):
        """ Calculates distortion maps 
            
        """
        
        cal_data = self.image_processor.cal_data
        size = (self.image_processor.isi.height, 
                self.image_processor.isi.width)
        
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
        self.map2 =self, self, self, self, self, self, self, self,  None
        self.rotation = None
        self.translation = None
        self.image_points = None
        self.object_points = None
    
    def save(self, file):
        logging.debug("%s %s %s %s %s %s %s %s" % (self.intrinsic, self.distortion, 
                 self.map1, self.map2, self.rotation, self.translation,
                 self.image_points, self.object_points))
        np.savez(file, self.intrinsic, self.distortion, 
                 self.map1, self.map2, self.rotation, self.translation,
                 self.image_points, self.object_points)

    def load(self, file):
       (self.intrinsic, self.distortion, self.map1, 
        self.map2, self.rotation, self.translation, self.image_points, 
        self.object_points) = np.load(file).files

    def __eq__(self):
        return self.rotation and self.translation and self.image_points == 6
