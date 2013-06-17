import cv2

class Camera:
    def __init__(self, name, cap_index, size):
        self.capture = cv2.VideoCapture(cap_index)
        self.name = name
        self.width = size[0]
        self.height = size[1]
        self.capture.set(3, self.width)
        self.capture.set(4, self.height)

    def read(self):
        _, frame = self.capture.read()
        return frame

    def __string__(self):
        return self.name
