import cv2
import time
import datetime
import logging

DEFAULT_OUTPUT_DIR = "../"
DEFAULT_IMG_EXT = "png"

class ImageSourceInterface(object):

    def __init__(self, image_processor, image_source):
        self.image_processor = image_processor
        self.config = image_processor.config
        self.image_source = image_source
        self.video_writer = None
        self.recording = False
        self.video_codec = self.config.get('video_file', 'video_codec')
        self.video_ext = self.config.get('video_file', 'video_ext')
        self.video_fps = self.config.get('video_file', 'video_fps')

    def read(self, flip=False):
        frame = self.image_source.read()
        if flip:
            frame = cv2.flip(frame, 1)
        if (self.video_writer and self.record):
            self.record(frame)
        return frame

    def save(self, filename="", frame=None):
        if not filename:
            time_stamp = datetime.datetime.fromtimestamp(
                    time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp, 
                        ".", DEFAULT_IMG_EXT])
        if frame is None:
            frame = self.read()
        cv2.imwrite(filename, frame)
    
    def startRecord(self, filename=""):
        if not filename:
            time_stamp = datetime.datetime.fromtimestamp(
                    time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp, 
                        ".", self.video_ext])
        self.video_writer = cv2.VideoWriter(filename, 
                                           cv2.cv.CV_FOURCC(*list(self.video_codec)),
                                           float(self.video_fps), (self.width, self.height))
        self.recording = True

    def stopRecord(self):
        self.video_writer = None
        self.recording = False

    def record(self, frame):
        if (self.video_writer.isOpened()):
            self.video_writer.write(frame)

    @property
    def width(self):
        return self.image_source.width
    
    @property
    def height(self):
        return self.image_source.height

    @property
    def name(self):
        return self.image_source.name

    def __string__(self):
        return self.image_source

    def __repr__(self):
        return '%s{%s (%d, %d)}' % (self.__class__, self.image_source.name,
                                    self.image_source.width,
                                    self.image_source.height)
