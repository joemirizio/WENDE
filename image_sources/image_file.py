import os
import sys
import cv2 as cv

#define image with a name, data, and dimensions
#ready in using CV, define window dim using shape library

class ImageFile:
    def __init__(self, filename):
        self.name = os.path.splitext(filename)[0]
        self.image = cv.imread(filename)
        if self.image is None:
            raise Exception('Invalid image file "%s"' % filename)
        self.height, self.width = self.image.shape[:2]

    def read(self):
        return self.image

    def __string__(self):
        return '%s{%s (%d, %d)}' % (self.__class__, self.name, self.width, self.height)
    def __repr__(self):
        return self.__string__()
