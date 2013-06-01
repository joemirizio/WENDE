import cv2 as cv
import numpy as np
import time
import datetime

DEFAULT_OUTPUT_DIR = "../"
DEFAULT_IMG_EXT = "png"

class Camera:
    def __init__(self, name, cap_index, size, position):
        self.capture = getCapture(cap_index)
        self.name = name
        self.width = size[0]
        self.height = size[1]
        self.capture.set(3, self.width)
        self.capture.set(4, self.height)
        self.video_writer = None
        self.recording = False
        self.intrinsic = []
        self.distortion = []
        self.rotation = []
        self.translation = []
        self.undistortMap = []
        self.position = None

    def read(self, flip=False):
        _, frame = self.capture.read()
        if flip:
            frame = cv.flip(frame, 1)
        if (self.video_writer and self.record):
            self.record(frame)
        #frame = cv.pyrDown(frame)
        return frame

    def save(self, filename="", frame=None):
        if not filename:
            time_stamp = datetime.datetime.fromtimestamp(
                    time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp, 
                        ".", DEFAULT_IMG_EXT])
        if frame is None:
            frame = self.read()
        cv.imwrite(filename, frame)
    
    def startRecord(self, filename="", fps=10):
        if not filename:
            time_stamp = datetime.datetime.fromtimestamp(
                    time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp, 
                        ".", "avi"])
        self.video_writer = cv.VideoWriter(filename, 
                                           cv.cv.CV_FOURCC('j', 'p', 'e', 'g'),
                                           fps, (self.width, self.height))
        self.recording = True

    def stopRecord(self):
        self.video_writer = None
        self.recording = False

    def record(self, frame):
        if (self.video_writer.isOpened()):
            self.video_writer.write(frame)
    
    def __string__(self):
        return '%s{%s (%d, %d)}' % (self.__class__, self.name, self.width, self.height)
    def __repr__(self):
        return self.__string__()


def getCapture(cap_index):
    return cv.VideoCapture(cap_index)
