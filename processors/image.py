import cv2 as cv
import numpy as np
import logging
import os


# Frames to conditionally display
FRAME_TYPES = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')

from data import DataProcessor
from display.gui.tkinter_gui import InputDialog
from calibration import SourceCalibrationModule
from detection import ObjectDetectionModule
from image_source import ImageSourceInterface
from image_sources import Camera
from image_sources import ImageFile
from image_sources import VideoFile


class ImageProcessor(object):

    def __init__(self, tca, image_source, frame_type=0):
        self.last_frame = None
        self.__avg_frame = None
        self.frame_type = FRAME_TYPES[frame_type]
        self.cal_data = None
        self.config = tca.config

        # Tactical Computer Application
        self.tca = tca
        # Image Source Interface
        self.isi = ImageSourceInterface(self, image_source)
        # Source Calibration Module
        self.scm = SourceCalibrationModule(self)
        # Object Detection Module
        self.odm = ObjectDetectionModule(self)
        
    def process(self):
        self.last_frame = self.isi.read()

        if self.avg_frame is None:
            self.avg_frame = self.last_frame

        # Find objects from the image source
        self.last_frame, self.avg_frame, img_data = self.odm.findObjects(
            self.last_frame, self.avg_frame, self.frame_type)

        # Display calibration points 
        if self.cal_data and self.frame_type == 'main':
            for num, cal_point in enumerate(self.cal_data.image_points, 1):
                point = (cal_point[0], cal_point[1])
                color_intensity = ((num - 1) % 3) / 3.0 * 200 + 55
                color = (0, 0, color_intensity) if num > 3 else (0, color_intensity, 0)
                cv.circle(self.last_frame, point, 5, color, thickness=-1)
                cv.circle(self.last_frame, point, 5, [0, 0, 0], thickness=2)

        # Display calibration status
        cal_status_color = [0, 255, 0] if self.cal_data else [0, 0, 255]
        cal_status_pos = (self.isi.width - 25, 25)
        cv.circle(self.last_frame, cal_status_pos, 20, [0, 0, 0], thickness=5) 
        cv.circle(self.last_frame, cal_status_pos, 20, cal_status_color, thickness=-1)
        cv.circle(self.last_frame, cal_status_pos, 20, [255, 255, 255], thickness=2) 

        self.tca.data_processor.process(img_data, self)

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

    def saveFrame(self, filename="", processed=True):
        self.isi.save(filename, self.last_frame if processed else None)

    def setFrameType(self, frame_type):
        if isinstance(frame_type, basestring):
            if frame_type in FRAME_TYPES:
                self.frame_type = frame_type
            else:
                raise Exception("Invalid frame type '%s'" % frame_type)
        else:
            self.frame_type = FRAME_TYPES[frame_type]

    def __string__(self):
        return 'Image Processor{%r}' % self.isi.image_source
    def __repr__(self):
        return self.__string__()


def createImageProcessors(tca):
    image_processors = []
    config = tca.config

    if (config.get('main', 'image_source') == 'CAMERA'):
        cam_offset = config.getint('camera', 'camera_offset')
        cam_count = config.getint('camera', 'camera_count')
        cam_size = (config.getint('camera', 'camera_size_x'),
                    config.getint('camera', 'camera_size_y'))
        for cap_index in range(cam_offset, cam_offset + cam_count):
            image_source = Camera('Cam' + str(cap_index), cap_index, cam_size)

    elif (config.get('main', 'image_source') == 'VIDEO_FILE'):
        video_files = config.get('video_file', 'video_files').split(',')
        for video_file_index, video_file in enumerate(video_files):
            video_size = (config.getint('video_file', 'video_size_x'),
                        config.getint('video_file', 'video_size_y'))
            video_name = 'Video' + str(video_file_index)
            image_source = VideoFile(video_name, video_file, video_size)
    else:
        img_files = config.get('image_file', 'image_files').split(',')
        for img_file in img_files:
            image_source = ImageFile(img_file)

    image_processor = ImageProcessor(tca, image_source)
    image_processors.append(image_processor)

    return image_processors
