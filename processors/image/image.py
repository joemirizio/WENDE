"""
The image processor coordinates actions of the Image Source Interface, the
Object Detection Module, and the Source Calibration Module.

After the appropriate image processors have been setup by the
createImageProcessors function, they retrieve images from selected sources
using the Image Source Interface. Images are then sent to the Object Detection
Module where the frames are scanned for potential target objects and returned.

The image processor overlays the calibration markers and associated
calibration status onto each frame as well.

Data collected by the image processor from the Object Detection Module is
delivered to the data processor for further analysis.

Classes:
    ImageProcessor

Functions:
    createImageProcessors()
"""
import cv2 as cv
import numpy as np
import logging
import os


# Frames to conditionally display
FRAME_TYPES = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')

from calibration import SourceCalibrationModule
from detection import ObjectDetectionModule
from detection import DetectionThreshold
from image_source import ImageSourceInterface
from image_sources import Camera
from image_sources import ImageFile
from image_sources import VideoFile


class ImageProcessor(object):
    """Coordinates actions of the Image Source Interface, the Object Detection
	Module, and the Source Calibration Module.

    Attributes:
        last_frame: An 8-bit image array containing the most recent frame.
        __avg_frame: An 8-bit image array that stores an average of previous
                     frames.
        frame_type: An string from the FRAME_TYPES list that describes a
                    property of the current frame.
        cal_data: A CalibrationData object.
        config: A SafeConfigParser object.
        tca: A Tactical Computer Application object.
        isi: An ImageSourceInterface object.
        scm: A SourceCalibrationModule object.
        odm: An ObjectDetectionModule object.

    Methods:
        process()
        avg_frame()
        avg_frame(frame)
        saveFrame()
        setFrameType()
        __string__()
        __repr__()
    """
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
	"""Reads in an image frame and searches for valid targets. Located
        targets are defined by enclosing contours, which are stored as
        vectors of points.
 
        Colored calibration circles are drawn in the corner of the frame to
        indicate the status of system calibration. Green circles mean
        calibration has been performed; Blue circles show a lack of system
        calibration.

        If calibration has been performed, then circles are drawn on the frame
        at points overlaying the visible calibration markers on the ground.

        Args:
            None

        Returns:
            An array storing the contour points of valid target objects.
        """

        self.last_frame = self.isi.read()

        if self.avg_frame is None:
            self.avg_frame = self.last_frame

        # Find objects from the image source
        self.last_frame, img_data = self.odm.findObjects(self.last_frame,
                                                         self.frame_type)
        
        if self.scm.getDisplayColors()[0]:
            center_threshold = DetectionThreshold(
                    self.scm.getCalibrationThresholds('center').min,
                    self.scm.getCalibrationThresholds('center').max)
            self.last_frame, img_data_center = self.odm.findObjects(self.last_frame,
                                                                    self.frame_type,
                                                                    center_threshold)
        if self.scm.getDisplayColors()[1]:
            side_threshold = DetectionThreshold(
                    self.scm.getCalibrationThresholds('side').min,
                    self.scm.getCalibrationThresholds('side').max)
            self.last_frame, img_data_side = self.odm.findObjects(self.last_frame,
                                                                  self.frame_type,
                                                                  side_threshold)

        # Display calibration points
        if self.cal_data.is_valid and self.frame_type == 'main':
            for num, cal_point in enumerate(self.cal_data.image_points, 1):
                point = (cal_point[0], cal_point[1])
                color_intensity = ((num - 1) % 3) / 3.0 * 200 + 55
                color = (0, 0, color_intensity) \
                if num > 3 else (0, color_intensity, 0)
                cv.circle(self.last_frame, point, 5, color, thickness=-1)
                cv.circle(self.last_frame, point, 5, [0, 0, 0], thickness=2)

        return img_data

    @property
    def avg_frame(self):
        """Currently returns the most recent image frame. Future
        development may return an average of previous image frames.       

        Args:
            None

        Returns:
            An 8-bit image array
        """
        return self.__avg_frame

    @avg_frame.setter
    def avg_frame(self, frame):
	"""Sets average frame using numpy float.       

        Args:
            frame: An 8-bit image array 
        """
        if self.__avg_frame is None:
            self.__avg_frame = np.float32(frame)
        else:
            self.__avg_frame = frame

    def saveFrame(self, filename="", processed=True):
	"""Saves current frame to an image file.       

        Args:
            filename: A string containing the name of the saved image file.
            processed: A boolean indicating whether or not the image has
                been processed.
        """
        self.isi.save(filename, self.last_frame if processed else None)

    def setFrameType(self, frame_type):
	"""Sets the frame type. 
        
        May be one of six options from the FRAME_TYPES list: 'main', 'orig',
        'blur', 'avg', 'gray', 'bw'        

        Args:
            frame_type: Either a string or an integer. A string will name the
                specific type while an integer will indicate the frame type 
                based on its order in the FRAME_TYPES list.   
        """
        if isinstance(frame_type, basestring):
            if frame_type in FRAME_TYPES:
                self.frame_type = frame_type
            else:
                raise Exception("Invalid frame type '%s'" % frame_type)
        else:
            self.frame_type = FRAME_TYPES[frame_type]

    def __string__(self):
	"""Returns a description of the image source. 
        
        Valid image sources are 'Camera', 'ImageFile', and 'VideoFile'.
        Example: Image Processor{Camera}  
        
        Args:
            None
            
        Returns:
            A string
        """
        return 'Image Processor{%r}' % self.isi.image_source

    def __repr__(self):
        """Returns a description of the image source. 
        
        Valid image sources are 'Camera', 'ImageFile', and 'VideoFile'.
        Example: Image Processor{Camera}  
        
        Args:
            None
            
        Returns:
            A string
        """
        return self.__string__()


def createImageProcessors(tca):
    """Initializes the current system image sources.
    
    Upon detection of the image source type, an ImageProcessor object is
    created for each source. These sources may be image files, video files,
    or live cameras.  
    
    Args:
        None
        
    Returns:
        An array of ImageProcessor objects.
    """
    image_processors = []
    config = tca.config

	# Camera(s) is configured
    if (config.get('main', 'image_source') == 'CAMERA'):
        cam_offset = config.getint('camera', 'camera_offset')
        cam_count = config.getint('camera', 'camera_count')
        cam_size = (config.getint('camera', 'camera_size_x'),
                    config.getint('camera', 'camera_size_y'))
        for cap_index in range(cam_offset, cam_offset + cam_count):
            image_source = Camera('Cam' + str(cap_index), cap_index, cam_size)
            image_processor = ImageProcessor(tca, image_source)
            image_processors.append(image_processor)

	# Video file(s) is configured
    elif (config.get('main', 'image_source') == 'VIDEO_FILE'):
        video_files = config.get('video_file', 'video_files').split(',')
        for video_file_index, video_file in enumerate(video_files):
            video_size = (config.getint('video_file', 'video_size_x'),
                          config.getint('video_file', 'video_size_y'))
            video_name = 'Video' + str(video_file_index)
            image_source = VideoFile(video_name, video_file, video_size)
            image_processor = ImageProcessor(tca, image_source)
            image_processors.append(image_processor)
			
	# Image(s) is configured
    else:
        img_files = config.get('image_file', 'image_files').split(',')
        for img_file in img_files:
            image_source = ImageFile(img_file)
            image_processor = ImageProcessor(tca, image_source)
            image_processors.append(image_processor)

    return image_processors
