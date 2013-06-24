"""
Defines a VideoFile object for retrieving a video input from a file.
A VideoFile object is created if the config.ini file has "VIDEO_FILE"
selected for the image source.

Classes:
    VideoFile
"""
import cv2


class VideoFile:
    """Retrieves video from a file

    Attributes:
        capture: An instance of VideoCapture that starts streaming from the
                 video file "filename".
        name: A string that identifies the specific video associated with
              an instance of this object (i.e. "Video1", "Video2", etc.).
        width: An integer indicating the pixel width of each video frame.
        height: An integer indicating the pixel height of each video frame.

    Methods:
        read()
        __string__()
    """
    def __init__(self, name, filename, size):
        self.capture = cv2.VideoCapture(filename)
        self.name = name
        self.width = size[0]
        self.height = size[1]
        # Sets size of video capture window
        self.capture.set(3, self.width)
        self.capture.set(4, self.height)

    def read(self):
        """Returns the next video frame from the corresponding video file.

        Args:
            None

        Returns:
            A single 8-bit image array
        """
        _, frame = self.capture.read()

        # Rewind video if the end has been reached
        if (self.capture.get(cv2.cv.CV_CAP_PROP_POS_FRAMES) ==
                self.capture.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)):
            self.capture.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0)

        return frame

    def __string__(self):
        """Returns a generic video name(i.e. "Video1", "Video2", etc.).

        Args:
            None

        Returns:
            A string
        """
        return self.name
