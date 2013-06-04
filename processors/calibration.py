import cv2 as cv
import numpy as np
import itertools as it
import logging
from math import sin, cos, pi
from image import ImageProcessor


SCALE = 12 # Scaling factor for global coordinates wrt feet, ex. 12 makes units inches, 1 makes unit feet
DISTS = (5, 10, 12)

# Constant values for calibration points with zero offset
LEFT_POINTS = [[dist * SCALE * x for x in (-1 * cos(pi/3), sin(pi/3))] for dist in DISTS]
CENTER_POINTS = [
    [0, 6],
    [0, 10],
    [0, 12]
    ]
RIGHT_POINTS = [[dist * SCALE * x for x in (cos(pi/3), sin(pi/3))] for dist in DISTS]

class Calibrator(object):

    def __init__(self, image_processors=None):
        self.leftPts = None
        self.centerPts = None
        self.rightPts = None
        
        if image_processors:
            self.calibrateImageProcessors(image_processors)


    def calibrateImageProcessors(self, image_processors):
        """ Calibrates input ImageProcessors
        
        Arguments:
            image_processors -- Image Processor objects
            
        """
        
        for imageProc in image_processors:
            # Intrinsic
            imageProc.loadIntrinsicParams()
            imageProc.calcDistortionMaps()

            # Extrinsic
            self.calcExtrinsicParams(imageProc, imageProc.x_offset, imageProc.y_offset)
            

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
    def calcExtrinsicParams(self, imageProc, xOffset, yOffset): 
        """ Collects images and calculates extrinsic parameters, storing them in ImageProcessor object
        
        Arguments: 
            imageProc -- ImageProcessor object
            xOffset -- Distance offset in x direction, specified in inches
            yOffset -- Distance offset in y direction, specified in inches
    
        """
        
        # Add offset and scaling to global coordinates if not already done
        if not self.leftPts:
            # Add necessary offset for global coordinate system (there should be no negative numbers...)
            self.leftPts = [[xOffset + point[0], yOffset + point[1]] for point in LEFT_POINTS]
            self.centerPts = [[xOffset + point[0], yOffset + point[1]] for point in CENTER_POINTS]
            self.rightPts = [[xOffset + point[0], yOffset + point[1]] for point in RIGHT_POINTS]
        
        # Append object points to array
        #if imageProc.position == left:
        objectPoints = np.array( (self.centerPts + self.leftPts), np.float32 )
        
        center_thresh_min = np.array([0, 0, 0], np.uint8)
        center_thresh_max = np.array([0, 0, 0], np.uint8)

        outside_thresh_min = np.array([0, 0, 0], np.uint8);
        outside_thresh_max = np.array([0, 0, 0], np.uint8);

        colors = [(center_thresh_min, center_thresh_max), 
                  (outside_thresh_min, outside_thresh_max)]
        #else:
            #objectPoints = np.array( (self.centerPts + self.rightPts), np.float32 )
        
        # Capture Image
        frame = imageProc.img_source.read()
        avg_frame = frame
        height, width = frame.shape[:2]
        
        # Find centers of calibration points
        calCenters = []
        for color in colors: ### TODO : IMPLEMENT SUCH THAT WE FILTER DIFFERENT COLORS FOR CENTER/SIDE
            # Get Contours
            _, _, contours = findObjects(frame, avg_frame,
                                imageProc.frame_type, 
                                color[0], color[1])
            
            # Get center points (Should get three, TODO : ADD EXCEPTION AND RETRY IF DIFFERENT)
            center, radius = cv.minEnclosingCircle(contours)
            calCenters.append(center)
        logging.log("Centers: %s" % calCenters)
        
        imagePoints = np.array( calCenters, np.float32 )
        
        # Calculate extrinsic parameters
        _, rvec, tvec = cv.solvePnP(objectPoints, imagePoints, imageProc.cal_data.intrinsic, imageProc.cal_data.distortion)
        rotation , _= cv.Rodrigues(rvec)
        translation = tvec
        
        # Store in camera object
        imageProc.cal_data.rotation = rotation
        imageProc.cal_data.translation = translation
