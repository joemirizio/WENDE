"""
Performs external calibration for the system.

By using pre-calculated intrinsic and distortion camera parameters along with
the location of ground calibration markers in the provided image frame, the
extrinsic system parameters are calculated. These parameters relate points in
the camera frame to global positions in the surveilled environment.
"""
import cv2 as cv
import numpy as np
import os
import logging
import pickle
from math import sin, cos, pi

from detection import DetectionThresholds

# CONSTANTS

# Scaling factor for global coordinates wrt feet,
# ex. 12 makes units inches, 1 makes unit feet
SCALE = 1
SIDE_ANGLE = pi/3  # 120 degrees
DISTANCES_NORMAL = (5, 10, 12)
DISTANCES_SMALL = (5, 6, 7)

SIDE_POINTS = [sin(SIDE_ANGLE), cos(SIDE_ANGLE), 0]
CENTER_POINTS = [0, 1, 0]

MIN_CAL_RADIUS = 8
ZERO_ARRAY = np.zeros((3), np.uint8)
ONE_ARRAY = np.ones((3), np.uint8)

class CalibrationThresholds(object):
    """ Holds calibration color minimum and maximum thresholds
    
    Attributes:
        center_min -- HSV values for center minimum threshold
        center_max -- HSV values for center maximum threshold
        side_min -- HSV values for center minimum threshold
        side_max -- HSV values for center maximum threshold
        
    Methods:
        setThresholds()
        getThresholds()
        
    """
    
    def __init__(self, center_min=None, center_max=None, side_min=None, side_max=None):
        
        self.center = DetectionThresholds(center_min, center_max)
        self.side = DetectionThresholds(side_min, side_max)
        
    def setThresholds(self, which_color, detect_min, detect_max, side_min=None, side_max=None):
        
        if which_color == 'center':
            self.center.setThresholds(detect_min, detect_max)
        elif which_color == 'side':
            self.side.setThresholds(detect_min, detect_max)
        elif which_color == 'all':
            self.center.setThresholds(detect_min, detect_max)
            self.side.setThresholds(side_min, side_max)
            
    def getThresholds(self, which_color=None):
        
        if which_color == 'center':
            return self.center
        elif which_color == 'side':
            return self.side
        else:
            return [self.center, self.side]

class SourceCalibrationModule(object):
    """Performs external calibration for the system.

    Attributes:
        image_processor: An imageProcessor object.
        config: A SafeConfigParser object.
        center_thresh_min: An array of the lower-limit RGB values expected for
            the demo calibration markers in the center region.
        center_thresh_max: An array of the upper-limit RGB values expected for
            the demo calibration markers in the center region.
        side_thresh_min: An array of the lower-limit RGB values expected for
            the demo calibration markers along the region sides.
        side_thresh_max: An array of the upper-limit RGB values expected for
            the demo calibration markers along the region sides.

    Methods:
        calibrate()
        getCalibration()
        getCalibrationPoints()
        calcExtrinsicParams()
        loadIntrinsicParams()
        getCalibrationDataFilename()
        saveCalibrationData()
        loadCalibrationData()
        calcDistortionMaps()
    """
    
    CAL_THRESHOLDS = CalibrationThresholds()
    DISPLAY_COLORS = False, False
    
    def __init__(self, image_processor):
        self.image_processor = image_processor
        self.config = image_processor.config

        # Expected color ranges of calibration markers
        center_thresh_min = np.array(self.config.get
                                     ('calibration', 'center_color_min').
                                     split(','), np.uint8)
        center_thresh_max = np.array(self.config.get
                                     ('calibration', 'center_color_max').
                                     split(','), np.uint8)
        side_thresh_min = np.array(self.config.get
                                   ('calibration', 'side_color_min').
                                   split(','), np.uint8)
        side_thresh_max = np.array(self.config.get
                                   ('calibration', 'side_color_max').
                                   split(','), np.uint8)
        
#         self.colors = [[center_thresh_min, center_thresh_max],
#                        [side_thresh_min, side_thresh_max]]

        # Initialize calibration colors to those in config file
        # This is no longer needed, but must initialize to something
        if self.getCalibrationThresholds()[0].min == None:
            self.setCalibrationThresholds('all', 
                                          [DetectionThresholds(center_thresh_min, 
                                                             center_thresh_max),
                                          DetectionThresholds(side_thresh_min,
                                                             side_thresh_max)])
        
        # Load pre-saved calibration data or create blank cal_data
        if self.config.getboolean('calibration', 'use_cal_data'):
            self.loadCalibrationData()
        else:
            # Create calibration data object
            self.image_processor.cal_data = CalibrationData()
            
        # Set calibration target distances
        if self.config.get('calibration', 'zone_size') == 'NORMAL':
            self.setCalibrationDistances(DISTANCES_NORMAL)
        elif self.config.get('calibration', 'zone_size') == 'SMALL':
            self.setCalibrationDistances(DISTANCES_SMALL)

    def calibrate(self, cal_points=None):
        """Calibrates the image processor
        
        Args: 
            cal_points -- list of lists containing calibration points
                [[x, y], [...], ...]
        """

        # Intrinsic
        self.loadIntrinsicParams()
        self.calcDistortionMaps()

        # Extrinsic
        if not cal_points:
            cal_points = self.getCalibrationPoints()
        self.calcExtrinsicParams(cal_points)
        

    def getCalibration(self):
        """Returns calibration data from image processors
        
        Args: 
            None.
        """
        return self.image_processor.cal_data

    def getCalibrationPoints(self):
        """Finds the pixel coordinates of calibration markers appearing in the captured image. 
        
        Args: 
            None.
        """
        # Capture Image
        frame = self.image_processor.isi.read()
        avg_frame = frame
        height, width = frame.shape[:2]

        # Find centroids of calibration points
        cal_points = []
        for color in self.getCalibrationThresholds():
            # Get Contours
            _, contours = self.image_processor.odm.findObjects(frame, 
                                                               self.image_processor.frame_type, 
                                                               color.min, 
                                                               color.max)

            # Get center points
            for contour in contours:
                center, radius = cv.minEnclosingCircle(contour)
                if radius > MIN_CAL_RADIUS:
                    cal_points.append(center)

        return cal_points

    def calcExtrinsicParams(self, cal_points):
        """Collects images and calculates extrinsic parameters, storing them in ImageProcessor object
        
        Args: 
            cal_points: A tuple containing the calibration points
        """
        # Verify image points are valid
        if not len(cal_points) == 6:
            logging.error("%s Calibration Failed: %d/6 points: %s" %
                          (self.image_processor.isi.name, len(cal_points),
                           cal_points))
            self.image_processor.cal_data.is_valid = False
            self.setDisplayColors(False, False)
            return

        # Create array from detected points
        imagePoints = np.array(cal_points, np.float32)

        # Determine whether left or right view and
        # create appropriate object points array.
        # Right Camera (center points farther left than side points)
        if cal_points[0][0] < cal_points[5][0]:
            objectPoints = np.array((self.center_points + self.right_points), np.float32)
        else:
            objectPoints = np.array((self.center_points + self.left_points), np.float32)
            
        # Calculate extrinsic parameters
        logging.debug("-------------------------------")
        logging.debug("objectPoints: %s" % objectPoints)
        logging.debug("imagePoint: %s" % imagePoints)
        logging.debug("intrinsic: %s"
                      % self.image_processor.cal_data.intrinsic)
        logging.debug("distortion: %s"
                      % self.image_processor.cal_data.distortion)
        _, rvec, tvec = cv.solvePnP(objectPoints, imagePoints,
                                    self.image_processor.cal_data.intrinsic,
                                    self.image_processor.cal_data.distortion)
        rotation, _ = cv.Rodrigues(rvec)
        translation = tvec

        # Store in camera object
        self.image_processor.cal_data.rotation = rotation
        self.image_processor.cal_data.translation = translation
        self.image_processor.cal_data.object_points = objectPoints
        self.image_processor.cal_data.image_points = imagePoints
        
        self.image_processor.cal_data.is_valid = True
        self.setDisplayColors(False, False)

    def loadIntrinsicParams(self):
        """Loads intrinsic matrix and distortion coefficients and calculates distortion map
        
        Args:
            None.
        """
        intrinsic_file = self.config.get('calibration', 'cal_intrinsic_file')
        distortion_file = self.config.get('calibration', 'cal_distortion_file')
        logging.debug('Loading intrinsic data from %s, %s' %
                      (intrinsic_file, distortion_file))
        self.image_processor.cal_data.intrinsic = np.loadtxt(intrinsic_file)
        self.image_processor.cal_data.distortion = np.loadtxt(distortion_file)

    def getCalibrationDataFilename(self):
        """Generates the calibration data filename and returns it. 
        
        Args:
            None.
            
        Return:
            A string containing the calibration data filename.
        """
        filename, ext = os.path.splitext(self.config.get("calibration",
                                                         "cal_data_file"))
        cal_filename = ''.join([filename, self.image_processor.isi.name, ext])
        return cal_filename

    def saveCalibrationData(self):
        """Saves calibration data to the calibration file. 
        
        Args:
            None.  
        """
        with open(self.getCalibrationDataFilename(), 'w') as cal_file:
            pickle.dump(self.image_processor.cal_data, cal_file)
            #self.image_processor.cal_data.save(cal_file)

    def loadCalibrationData(self):
        """Loads calibration data from the calibration file. 
        
        Args:
            None.  
        """
        with open(self.getCalibrationDataFilename(), 'r') as cal_file:
            self.image_processor.cal_data = pickle.load(cal_file)
            #self.image_processor.cal_data.load(cal_file)

    def calcDistortionMaps(self):
        """Calculates distortion maps used for distortion compensation. 
        
        Args:
            None.  
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
        
    def setCalibrationThresholds(self, which_color, cal_thresholds):
        """ Sets new HSV values used to find calibration points
        
        Arguments:
            cal_thresholds -- List of color detection thresholds. List contains
                either one or two DetectionThreshold objects
                
        """
        
        if which_color == 'all':
            SourceCalibrationModule.CAL_THRESHOLDS.setThresholds('all', 
                                                             cal_thresholds[0].min, 
                                                             cal_thresholds[0].max,
                                                             cal_thresholds[1].min, 
                                                             cal_thresholds[1].max)
        elif which_color == 'center' or 'side':
            SourceCalibrationModule.CAL_THRESHOLDS.setThresholds(which_color, 
                                                             cal_thresholds[0].min, 
                                                             cal_thresholds[0].max)
        
    def getCalibrationThresholds(self, which_color=None):
        """ Gets HSV values used to find calibration points
        
        Arguments:
            which_color -- 'center', 'side', to get just one threshold, or None
                to return both objects
        
        Return Values:
            thresholds -- List of DetectionThreshold objects. List length is
                determined by which_color argument. Organized as center, side
                
        """
        
        if not which_color:
            thresholds = SourceCalibrationModule.CAL_THRESHOLDS.getThresholds()
        else:
            thresholds = SourceCalibrationModule.CAL_THRESHOLDS.getThresholds(which_color)
        
        return thresholds
    
    def setDisplayColors(self, bool_center, bool_side):
        """ Sets class attribute for calibration color display
        
        Arguments:
            bool -- boolean True or False
            
        """
        
        SourceCalibrationModule.DISPLAY_COLORS = bool_center, bool_side
        
    def getDisplayColors(self):
        """ Gets current value for display colors class attribute """
        
        return SourceCalibrationModule.DISPLAY_COLORS
    
    def setCalibrationDistances(self, zone_distances=(5, 10, 12)):
        """ Sets Distances for safe, alert, and prediction zone boundaries
        
        Arguments:
            zone_size -- Three element iterable containing boundary lengths
            
        """
        
        # Calibration point position calculations
        DISTANCES = [distance * SCALE for distance in zone_distances]
        
        # Location of calibration markers in global coordinates
        self.right_points = [[distance * coordinate for coordinate in SIDE_POINTS]
                        for distance in DISTANCES]
        self.center_points = [[distance * coordinate for coordinate in CENTER_POINTS]
                         for distance in DISTANCES]
        self.left_points = [[-1 * x, y, z] for x, y, z in self.right_points]

class CalibrationData(object):
    """Saves or loads calibration data to/from file.

    Attributes:
        intrinsic: A multi-channel 2D matrix of the intrinsic camera parameters.
        distortion: A multi-channel 2D matrix of the camera distortion parameters.
        map1: An array of the undistortion transformation map.
        map2: An array of the rectification transformation map.
        rotation: An array of the rotation parameters.  
        translation: An array of the translation parameters.
        image_points: An integer indicating the number of calibration markers seen in the image.
        object_points: An array containing the position coordinates for calibration points.
        is_valid: Boolean value defining whether object contains valid calibration data 
    
    Methods:
        save()
        load()
        __eq__()
    """
    def __init__(self):
        self.intrinsic = None
        self.distortion = None
        self.map1 = None
        self.map2 = None
        self.rotation = None
        self.translation = None
        self.image_points = None
        self.object_points = None
        self.is_valid = False

    def save(self, file):
        """Saves the calibration data to a text file. 
        
        Args:
            file: A string containing the file name where the data will be saved.  
        """
        logging.debug("%s %s %s %s %s %s %s %s" % (self.intrinsic,
                                                   self.distortion,
                                                   self.map1, self.map2,
                                                   self.rotation,
                                                   self.translation,
                                                   self.image_points,
                                                   self.object_points))
        np.savez(file, self.intrinsic, self.distortion,
                 self.map1, self.map2, self.rotation, self.translation,
                 self.image_points, self.object_points)

    def load(self, file):
        """Loads the calibration data from a text file. 
        
        Args:
            file: A string containing the file name from which the data will be retrieved.  
        """
        (self.intrinsic, self.distortion, self.map1,
         self.map2, self.rotation, self.translation, self.image_points,
         self.object_points) = np.load(file).files
        
        self.is_valid = True

    def __eq__(self):
        """Checks to see if calibration data is present. 
        
        Args:
            None.
            
        Returns:
            A boolean
        """
        return self.rotation and self.translation and self.image_points == 6
