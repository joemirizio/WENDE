import cv2 as cv
import numpy as np
import time
import datetime

DEFAULT_OUTPUT_DIR = "../"
DEFAULT_IMG_EXT = "png"

class VideoFile:
    def __init__(self, name, filename, size):
        self.capture = getCapture(filename)
        self.name = name
        self.width = size[0]
        self.height = size[1]
        self.capture.set(3, self.width)
        self.capture.set(4, self.height)

    def read(self, flip=False):
        _, frame = self.capture.read()
        if flip:
            frame = cv.flip(frame, 1)
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
    
    def __string__(self):
        return '%s{%s (%d, %d)}' % (self.__class__, self.name, self.width, self.height)
    def __repr__(self):
        return self.__string__()


def getCapture(filename):
    return cv.VideoCapture(filename)
