import cv2

class VideoFile:
    def __init__(self, name, filename, size):
        self.capture = cv2.VideoCapture(filename)
        self.name = name
        self.width = size[0]
        self.height = size[1]
        self.capture.set(3, self.width)
        self.capture.set(4, self.height)

    def read(self):
        _, frame = self.capture.read()

        # Rewind video if the end has been reached
        if (self.capture.get(cv2.cv.CV_CAP_PROP_POS_FRAMES) ==
            self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)):
            self.capture.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0)
            
        return frame

    def __string__(self):
        return self.name
