"""
Defines an ImageSourceInterface object that is the point of interaction
between the processing algorithms and the three potential image sources: a
camera, a video file, or an image file. The interface enables bidirectional
movement of images, pre-recorded video, or live camera feed, depending upon
which image source is selected.

Image frames from various sources can be read in for processing. After
processing, frames can be either saved as single images (PNG by default) or
compiled into video files (file type controlled in config.ini; avi by
default).

Classes:
    ImageSourceInterface
"""
import cv2
import time
import datetime
import logging

DEFAULT_OUTPUT_DIR = "../"
DEFAULT_IMG_EXT = "png"


class ImageSourceInterface(object):
    """Acts as the point of interaction between the processing algorithms and
    image sources.

    Attributes:
        image_processor: An ImageProcessor object.
        config: A SafeConfigParser object.
        image_source: Either a Camera, ImageFile, or VideoFile object.
        video_writer: An instance of VideoWriter that writes
            recorded video to a file. It will contain "None" when video is not
            being recorded.
        recording: A boolean indicating whether video is being recorded.
        video_codec: A string that determines the codec of recorded video.
        video_ext: A string that determines the file extension of
            recorded video.
        video_fps: An integer that determines the frames per second of
            recorded video.

    Methods:
        read()
        save()
        startRecord()
        stopRecord()
        record()
        width()
        height()
        name()
        __string__()
        __repr__()
    """
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
        """Reads in a frame from the image source and returns it.

        The frame will be mirrored if the argument "flip" is true. The frame
        will be written to a video file if "video_writer" and record()
        indicate an active writing state.

        Args:
            flip: A boolean that determines whether images/frames are
                  flipped or mirrored when read.

        Returns:
            A single 8-bit image array

        Raises:
            IOError: Unable to read image source.
        """
        frame = self.image_source.read()
        if flip:
            frame = cv2.flip(frame, 1)
        # Checks for an active writing state.
        if (self.video_writer and self.record):
            self.record(frame)
        if frame is None:
            raise IOError('Unable to read image source %s' % self.name)
        return frame

    def save(self, filename="", frame=None):
        """Writes a frame to an image file.

        If no filename argument is provided, a filename is automatically
        created using the default output directory, the image_source name, a
        time stamp, and the default image extension. An example would be:
                            filename_2013-06-13_20-47-57.png
        If no frame is provided, one is automatically read in.

        Args:
            filename: A string that names the saved image file.
            frame: An 8-bit array of the image to be saved. It will contain
                   "None" when no frame is provided.
        """
        if not filename:
            time_stamp = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp,
                               ".", DEFAULT_IMG_EXT])
        if frame is None:
            frame = self.read()
        cv2.imwrite(filename, frame)

    def startRecord(self, filename=""):
        """Creates and initializes a file to contain recorded video.

        If no filename argument is provided, a filename is automatically
        created using the image_source name, a time stamp, and the default
        video extension. An example would be:
                            Cam2_2013-06-13_20-47-57.avi
        Args:
            filename: A string that names the recorded video file.
        """
        if not filename:
            time_stamp = datetime.datetime.fromtimestamp(
                time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            filename = "".join([DEFAULT_OUTPUT_DIR, self.name, "_", time_stamp,
                               ".", self.video_ext])
        self.video_writer = cv2.VideoWriter(
            filename, cv2.cv.CV_FOURCC(*list(self.video_codec)),
            float(self.video_fps), (self.width, self.height))
        self.recording = True

    def stopRecord(self):
        """Stops video recording

        Args:
            None
        """
        self.video_writer = None
        self.recording = False

    def record(self, frame):
        """Records a frame to a video file if the file is currently
           open for writing.

        Args:
            frame: An 8-bit image array
        """
        if (self.video_writer.isOpened()):
            self.video_writer.write(frame)

    @property
    def width(self):
        """Returns the pixel width of the image source.

        Args:
            None

        Returns:
            An integer
        """
        return self.image_source.width

    @property
    def height(self):
        """Returns the pixel height of the image source.

        Args:
            None

        Returns:
            An integer
        """
        return self.image_source.height

    @property
    def name(self):
        """Returns the name of the image source (i.e. "Cam1", "Video2", etc.).

        Args:
            None

        Returns:
            A string
        """
        return self.image_source.name

    def __string__(self):
        """Returns the name of the image source (i.e. "Cam1", "Video2", etc.).

        Args:
            None

        Returns:
            A string
        """
        return self.image_source.__string__()

    def __repr__(self):
        """Returns a description of the active image source. An example:
                    ImageSourceInterface{Cam1 (800, 600)}
        Args:
            None

        Returns:
            A string
        """
        return '%s{%s (%d, %d)}' % (self.__class__, self.image_source.name,
                                    self.image_source.width,
                                    self.image_source.height)

