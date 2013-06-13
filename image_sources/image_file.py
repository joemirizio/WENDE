import os
import cv2

class ImageFile:
    def __init__(self, filename):
        self.name = os.path.splitext(filename)[0]
        self.image = cv2.imread(filename)
        if self.image is None:
            raise Exception('Invalid image file "%s"' % filename)
        self.height, self.width = self.image.shape[:2]

    def read(self):
        return self.image

    def __string__(self):
        return self.name

