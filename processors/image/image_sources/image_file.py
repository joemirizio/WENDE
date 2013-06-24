"""
Defines an ImageFile object for retrieving an image input from a file.
An ImageFile object is created if the config.ini file has "IMAGE_FILE"
selected for the image source.

Classes:
    ImageFile
"""
import os
import cv2


class ImageFile:
    """Retrieves an image from a file

    Attributes:
        name: A string of the image file name, without the file extension.
        image: An array that stores the 8-bit image aquired by imread().
        height: An integer indicating the pixel height of the image.
        width: An integer indicating the pixel width of the image.

    Methods:
        read()
        __string__()
    """
    def __init__(self, filename):
        self.name = os.path.splitext(filename)[0]
        self.image = cv2.imread(filename)
        # Display error message if image read fails.
        if self.image is None:
            raise Exception('Invalid image file "%s"' % filename)
        # Determine image size
        self.height, self.width = self.image.shape[:2]

    def read(self):
        """Returns the acquired image.

        Args:
            None

        Returns:
            An 8-bit image array
        """
        return self.image

    def __string__(self):
        """Returns the image file name, without the extension.

        Args:
            None

        Returns:
            A string
        """
        return self.name
