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
DETECT_MIN = np.array([124, 98, 40], np.uint8)
DETECT_MAX = np.array([255, 236, 244], np.uint8)

# Minimum dimensions of bounded contours
CONTOUR_MIN_WIDTH = 5
CONTOUR_MIN_HEIGHT = 5


class ObjectDetectionModule(object):
    """Scans an image for potential targets and provides size/location
	information about these targets.

    Attributes:
        image_processor: An ImageProcessor object.
        config: A SafeConfigParser object.

    Methods:
        findObjects()
    """
    def __init__(self, image_processor):
        self.image_processor = image_processor
        self.config = image_processor.config

    def findObjects(self, frame, frame_type=FRAME_TYPES[0],
                    detectMin=DETECT_MIN, detectMax=DETECT_MAX):
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
            detectMin = An array serving as the lower threshold in the binary
                filtering.
            detectMin = An array serving as the upper threshold in the binary
                filtering.

        Returns:
            A two-element tuple whose first element is the original 8-bit
            image frame with contours and bounding boxes drawn. The second
            element is an array containing vectors of contour points.
        """
        blur_frame = cv.GaussianBlur(frame, (19, 19), 0)
        hsv_frame = cv.cvtColor(blur_frame, cv.COLOR_BGR2HSV)
        
        # Find pixels in defined HSV ranges
        if detectMin[0] < detectMax[0]:
            thresh_frame = cv.inRange(hsv_frame, detectMin, detectMax)
        
        else:
            # If the hue is wrapped, process separately from saturation, value (brightness)
            channel_hue = hsv_frame[:,:,0]
            thresh_hue = np.logical_not(cv.inRange(channel_hue, 
                                                   detectMax[0], 
                                                   detectMin[0]))
            thresh_sv = cv.inRange(hsv_frame[:,:,1:],
                                   detectMin[1:],
                                   detectMax[1:])
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
        threshold_seed -- list containing HSV value to build thresholds around
        
    Outputs:
        detection_min, detection_max -- 3x1 numpy arrays containing HSV values
            defining the detection thresholds
            
    """
    
    # Define HSV range for thresholds
    delta_hsv = np.array([5, 50, 75], np.int16)
    
    color_input = np.array(threshold_seed, np.int16)
    detect_min = detect_max = np.empty((3), np.int16)
    
    # Allow hue value to wrap
    detect_min = color_input - delta_hsv
    detect_max = color_input + delta_hsv
    
    # Wrap hsv
    if detect_min[0] < 0: detect_min[0] = (180 + detect_min[0])
    if detect_max[0] > 180: detect_max[0] = detect_max[0] - 180
    
    # Cap saturation and threshold values
    for index in xrange(1, 3):
        if detect_min[index] < 0: detect_min[index] = 0
        if detect_max[index] > 255: detect_max[index] = 255
        
    return detect_min.astype(np.uint8), detect_max.astype(np.uint8)
    
### This is for blob detection, currently unused
##    def processImage(self, frame, avg_frame, frame_type=FRAME_TYPES[0]):
##        # Blur and average with previous frames
##        src_frame = cv.GaussianBlur(frame, (19, 19), 0)
##        cv.accumulateWeighted(src_frame, avg_frame, AVG_WEIGHT)
##        conv_frame = cv.convertScaleAbs(avg_frame)
##
##        # Subtract current and average frames
##        diff_frame = cv.absdiff(src_frame, conv_frame)
##
##        # Convert to grayscale then to black/white
##        gray_frame = cv.cvtColor(diff_frame, cv.COLOR_RGB2GRAY)
##        _, bw_frame = cv.threshold(gray_frame, BW_THRESHOLD, 255,
##                                   cv.THRESH_BINARY)
##
##        # Calculate contours
##        bw_copy = bw_frame.copy()
##        contours, hier = cv.findContours(bw_copy, cv.RETR_EXTERNAL,
##                                         cv.CHAIN_APPROX_SIMPLE)
##
##        # Draw countours and bounding boxes
##        main_frame = frame.copy()
##        for contour in contours:
##            rect = cv.boundingRect(contour)
##            top  = rect[0:2]
##            bot  = (rect[0] + rect[2], rect[1] + rect[3])
##            cv.rectangle(main_frame, top, bot, (255, 0, 0), 1)
##        cv.drawContours(main_frame, contours, -1, (0, 255, 0), -1)
##
##        # Select desired frame to display
##        frames = dict(zip(FRAME_TYPES, (main_frame, frame, src_frame,
##                                        conv_frame, gray_frame, bw_frame)))
##        out_frame = frames[frame_type]
##
##        return (out_frame, avg_frame, contours
