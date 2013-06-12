import cv2 as cv
import numpy as np

from image import FRAME_TYPES

AVG_WEIGHT = 0.01
BW_THRESHOLD = 20

DETECT_MIN = np.array([26, 94, 105], np.uint8)
DETECT_MAX = np.array([101, 203, 169], np.uint8)

class ObjectDetectionModule(object):

    def __init__(self, image_processor, config):
        self.image_processor = image_processor
        self.config = config

    def findObjects(self, frame, avg_frame, frame_type=FRAME_TYPES[0],
                    detectMin=DETECT_MIN, detectMax=DETECT_MAX):
        blur_frame = cv.GaussianBlur(frame, (19, 19), 0)
        hsv_frame = cv.cvtColor(blur_frame, cv.COLOR_BGR2HSV)
        thresh_frame = cv.inRange(hsv_frame, detectMin, detectMax)

        # Calculate contours
        bw_copy = thresh_frame.copy()
        contours, hier = cv.findContours(bw_copy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # Draw countours and bounding boxes
        main_frame = frame.copy()
        for contour in contours:
            rect = cv.boundingRect(contour)
            top  = rect[0:2]
            bot  = (rect[0] + rect[2], rect[1] + rect[3])
            cv.rectangle(main_frame, top, bot, (255, 0, 0), 1)
        cv.drawContours(main_frame, contours, -1, (0, 255, 0), -1)

        frames = dict(zip(FRAME_TYPES, (main_frame, frame, thresh_frame)))
        out_frame = frames[frame_type]


        return (out_frame, avg_frame, contours)
        
    def processImage(self, frame, avg_frame, frame_type=FRAME_TYPES[0]):
        # Blur and average with previous frames
        src_frame = cv.GaussianBlur(frame, (19, 19), 0)
        cv.accumulateWeighted(src_frame, avg_frame, AVG_WEIGHT)
        conv_frame = cv.convertScaleAbs(avg_frame)

        # Subtract current and average frames
        diff_frame = cv.absdiff(src_frame, conv_frame)

        # Convert to grayscale then to black/white
        gray_frame = cv.cvtColor(diff_frame, cv.COLOR_RGB2GRAY)
        _, bw_frame = cv.threshold(gray_frame, BW_THRESHOLD, 255, cv.THRESH_BINARY)

        # Calculate contours
        bw_copy = bw_frame.copy()
        contours, hier = cv.findContours(bw_copy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # Draw countours and bounding boxes
        main_frame = frame.copy()
        for contour in contours:
            rect = cv.boundingRect(contour)
            top  = rect[0:2]
            bot  = (rect[0] + rect[2], rect[1] + rect[3])
            cv.rectangle(main_frame, top, bot, (255, 0, 0), 1)
        cv.drawContours(main_frame, contours, -1, (0, 255, 0), -1)

        # Select desired frame to display
        frames = dict(zip(FRAME_TYPES, (main_frame, frame, src_frame, conv_frame, gray_frame, bw_frame)))
        out_frame = frames[frame_type]

        return (out_frame, avg_frame)

        
