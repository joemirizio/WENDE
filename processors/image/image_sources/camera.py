"""
Defines a Camera object for accepting video feed input from a system webcam.
A camera object is created if the config.ini file has "CAMERA" selected for
the image source.

Classes:
    Camera
"""
import cv2


class Camera:
    """Accepts video feed input from a system webcam

    Attributes:
        capture: An instance of VideoCapture that starts streaming from the
                 camera assigned the identifying number "cap_index".
        name: A string that identifies the specific camera associated with
              an instance of this object (i.e. "Cam1", "Cam2", etc.).
        width: An integer indicating the pixel width of each camera frame.
        height: An integer indicating the pixel height of each camera frame.

    Methods:
        read()
        __string__()
    """
    def __init__(self, name, cap_index, size):
        self.capture = cv2.VideoCapture(cap_index)
        self.name = name
        self.width = size[0]
        self.height = size[1]
        self.capture.set(3, self.width)
        self.capture.set(4, self.height)

    def read(self):
        """Returns the next video frame from the corresponding camera source.

        Args:
            None

        Returns:
            A single 8-bit image array
        """
        _, frame = self.capture.read()
        return frame

    def __string__(self):
        """Returns the camera name (i.e. "Cam1", "Cam2", etc.).

        Args:
            None

        Returns:
            A string
        """
        return self.name
