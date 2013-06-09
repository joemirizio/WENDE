import cv2 as cv
import numpy as np
import logging
import os

# Frames to conditionally display
FRAME_TYPES = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')

from data import DataProcessor
from processors.calibration import SourceCalibrationModule
from display.gui.tkinter_gui import InputDialog
from processors.CalibrationData import CalibrationData
from processors.detection import ObjectDetectionModule

class ImageProcessor(object):

    def __init__(self, tca, img_source, config=None, frame_type=0, data_proc=None):
        self.img_source = img_source
        self.last_frame = None
        self.__avg_frame = None
        self.frame_type = FRAME_TYPES[frame_type]
        self.cal_data = None

        # Tactical Computer Application
        self.tca = tca
        # Source Calibration Module
        self.scm = SourceCalibrationModule(self, config)
        # ObjectDetectionModule
        self.odm = ObjectDetectionModule(self, config)

        self.config = config
        
        if data_proc is None:
            self.data_proc = DataProcessor()
        else:
            self.data_proc = data_proc
    
    def process(self):
        self.last_frame = self.img_source.read()

        if self.avg_frame is None:
            self.avg_frame = self.last_frame

        # Find objects from the image source
        self.last_frame, self.avg_frame, img_data = self.odm.findObjects(
            self.last_frame, self.avg_frame, self.frame_type)

        # Display calibration points 
        if self.cal_data and self.frame_type == 'main':
            for num, cal_point in enumerate(self.cal_data.image_points, 1):
                point = (cal_point[0], cal_point[1])
                color = (0, 0, 255) if num > 3 else (0, 255, 0)
                cv.circle(self.last_frame, point, 5, color, thickness=-1)
                cv.circle(self.last_frame, point, 5, [0, 0, 0], thickness=2)

        self.data_proc.process(img_data, self)

        return self.last_frame

    @property
    def avg_frame(self):
                #define average frame property to be used in process
        return self.__avg_frame
    @avg_frame.setter
    def avg_frame(self, frame):
                #set average frame using numpy float
        if self.__avg_frame is None:
            self.__avg_frame = np.float32(frame)
        else:
            self.__avg_frame = frame

    def saveFrame(self, filename=""):
        self.img_source.save(filename, self.last_frame)

    def setFrameType(self, frame_type):
        if isinstance(frame_type, basestring):
            if frame_type in FRAME_TYPES:
                self.frame_type = frame_type
            else:
                raise Exception("Invalid frame type '%s'" % frame_type)
        else:
            self.frame_type = FRAME_TYPES[frame_type]

    def __string__(self):
        return 'Image Processor{%r}' % self.image_source
    def __repr__(self):
        return self.__string__()

