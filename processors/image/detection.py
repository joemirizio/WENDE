"""
The object detection module scans an image for potential targets and provides
information about these targets.

Images passed to the object detection module are blurred and converted to a
saturation display format. (This enhances the contrast of color variations
appearing in the original image.) The resulting image is then binary filtered
to isolate a certain color hue that is characteristic of target objects. Any
contours are detected on the filtered image and are overlayed onto original,
unaltered frame. Rectangular bounding boxes enclosing each contour are also
drawn before returning the frame.

Classes:
    ObjectDetectionModule
"""
import cv2 as cv
import numpy as np
import logging as logging

from image import FRAME_TYPES

# AVG_WEIGHT = 0.01
# BW_THRESHOLD = 20

# Binary filter threshold limits
TARGET_THRESHOLD_MIN = [124, 98, 40]
TARGET_THRESHOLD_MAX = [255, 236, 244]

# DETECT_MIN = np.array([124, 98, 40], np.uint8)
# DETECT_MAX = np.array([255, 236, 244], np.uint8)

# Delta values for threshold building
DELTA_HSV = np.array([10, 50, 75], np.int16)

# Minimum dimensions of bounded contours
CONTOUR_MIN_WIDTH = 5
CONTOUR_MIN_HEIGHT = 5

class DetectionThreshold(object):
    """ Storage container for minimum and maximum detection thresholds
    
    Attributes:
        min -- HSV values for detection minimum threshold
        max -- HSV values for detection maximum threshold
        
    Methods:
        getThresholds()
        
    """
    
    def __init__(self, detect_min=None, detect_max=None):
        
        if not detect_min is None:
            self.min = np.array(detect_min, np.uint8)
            self.max = np.array(detect_max, np.uint8)
        else:
            self.min = detect_min
            self.max = detect_max
        
    def setThresholds(self, detect_min, detect_max):
        self.min = np.array(detect_min, np.uint8)
        self.max = np.array(detect_max, np.uint8)
        
    def getThresholds(self):
        return self.min, self.max

class ObjectDetectionModule(object):
    """Scans an image for potential targets and provides size/location
	information about these targets.

    Attributes:
        image_processor: An ImageProcessor object.
        config: A SafeConfigParser object.

    Methods:
        findObjects()
    """
    
    TARGET_THRESHOLDS = DetectionThreshold(TARGET_THRESHOLD_MIN, TARGET_THRESHOLD_MAX)
    
    def __init__(self, image_processor):
        self.image_processor = image_processor
        self.config = image_processor.config

    def findObjects(self, frame, frame_type=FRAME_TYPES[0],
                    detection_threshold=TARGET_THRESHOLDS):
	"""A frame is scanned for target objects by finding contours, which
        are then drawn on the frame.

        Takes the provided image frame, applies a Gaussian blur, and
        converts it to a saturation display format. The resulting
        image is then binary filtered to isolate a certain color hue
        (currently hot pink) characteristic of target objects. Any contours
        are detected on the filtered image and are overlayed onto original,
        unaltered frame. Rectangular bounding boxes enclosing sufficiently
        large contours are also drawn.

        Args:
            frame: An 8-bit image array of the frame to be processed.
            frame_type: An string from the FRAME_TYPES list that describes a
                property of the current frame.
            detection_threshold: The min and max threshold for binary filtering
        Returns:
            A two-element tuple whose first element is the original 8-bit
            image frame with contours and bounding boxes drawn. The second
            element is an array containing vectors of contour points.
        """
        blur_frame = cv.GaussianBlur(frame, (19, 19), 0)
        hsv_frame = cv.cvtColor(blur_frame, cv.COLOR_BGR2HSV)
        
        detect_min = detection_threshold.min
        detect_max = detection_threshold.max

        # Find pixels in defined HSV ranges
        if detect_min[0] < detect_max[0]:
            thresh_frame = cv.inRange(hsv_frame, detect_min, detect_max)
        
        else:
            # If the hue is wrapped, process separately from saturation, value (brightness)
            channel_hue = hsv_frame[:,:,0]
            thresh_hue = np.logical_not(cv.inRange(channel_hue, 
                                                   np.array(detect_max[0]), 
                                                   np.array(detect_min[0])))
            thresh_sv = cv.inRange(hsv_frame[:,:,1:],
                                   detect_min[1:],
                                   detect_max[1:])
            # Logical combination of the two thresholds, cast into uint8 for findContours
            thresh_frame = np.logical_and(thresh_hue, thresh_sv).astype(np.uint8)
            
        # Calculate contours
        thresh_copy = thresh_frame.copy()
        contours, hier = cv.findContours(thresh_copy, cv.RETR_EXTERNAL,
                                         cv.CHAIN_APPROX_SIMPLE)

        # Draw countours and bounding boxes
        main_frame = frame.copy()
        filtered_contours = []
        for contour in contours:
            rect = cv.boundingRect(contour)
            if rect[1] > CONTOUR_MIN_WIDTH and rect[3] > CONTOUR_MIN_HEIGHT:
                top = rect[0:2]  # Top left corner
                bot = (rect[0] + rect[2], rect[1] + rect[3])  # Lwr rght corner
                cv.rectangle(main_frame, top, bot, (0, 255, 0), 1)
                np.append(filtered_contours, contour)
        cv.drawContours(main_frame, contours, -1, (255, 0, 0), -1)

##        for contour in contours:
##            rect = cv.boundingRect(contour)
##            top  = rect[0:2] # Top left corner
##            bot  = (rect[0] + rect[2], rect[1] + rect[3]) # Lwr right corner
##            if rect[2]>CONTOUR_MIN_WIDTH and rect[3]>CONTOUR_MIN_HEIGHT:
##                cv.rectangle(main_frame, top, bot, (0, 255, 0), 1)
##        cv.drawContours(main_frame, contours, -1, (255, 0, 0), -1)

        frames = dict(zip(FRAME_TYPES, (main_frame, frame, thresh_frame)))
        out_frame = frames[frame_type]

        return (out_frame, contours)

def buildDetectionThresholds(threshold_seed):
    """ Creates detection min and max corresponding to input color
    
    Arguments:
        color_seed -- list containing HSV value to build thresholds around
        
    Outputs:
        detection_thresholds -- DetectionThreshold object
            
    """
    
    color_input = np.array(threshold_seed, np.int16)
    detect_min = detect_max = np.empty((3), np.int16)
    
    # Allow hue value to wrap
    detect_min = color_input - DELTA_HSV
    detect_max = color_input + DELTA_HSV
    
    # Wrap hsv
    if detect_min[0] < 0: detect_min[0] = (180 + detect_min[0])
    if detect_max[0] > 180: detect_max[0] = detect_max[0] - 180
    
    # Cap saturation and threshold values
    for index in xrange(1, 3):
        if detect_min[index] < 0: detect_min[index] = 0
        if detect_max[index] > 255: detect_max[index] = 255
        
    detection_thresholds = DetectionThreshold(detect_min, detect_max)
        
    return detection_thresholds
