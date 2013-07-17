"""
The data processor processes the information received from the image
processors and provides the result to the Target Track Module.

All detections from the image processors are filtered through the Target
Discrimination Module and the Target Correlation Module. The resulting
finalized position list is then provided to the Target Track Module
for track assignment and updating.

Additional functionality converts image coordinates into the global
reference frame and also removes image source distortion.

Classes:
    DataProcessor

Functions:
    distance()
    undistortImage()
    convertToGlobal()
"""
import math
import logging
import numpy as np
import cv2

from discrimination import TargetDisciminationModule
from track import TargetTrackModule
from target import Target
from correlation import TargetCorrelationModule

AREA_THRESHOLD = 50
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075
POS_THRESHOLD = 0.05


class DataProcessor(object):
    """Processes the data received from the image processors and provides it
    to the Target Track Module.

    All detections from the image processors are filtered through the Target
    Discrimination Module and the Target Correlation Module. The resulting
    finalized position list is then provided to the Target Track Module
    for track assignment and updating. A method for erasing all target data
    is also provided.

    Attributes:
        targets: A list of stored Target objects.
        coverages:
        tca: A Tactical Computer Application object.
        config: A SafeConfigParser object.
        is_active: A boolean indicating the activity status of the data
            processor.
        tcm: A TargetCorrelationModule object.
        tdm: A TargetDisciminationModule object.
        ttm: A TargetTrackModule object.

    Methods:
        process()
        clearTargetData()
        toggleActive()
    """
    def __init__(self, tca):
        self.targets = []
        self.coverages = {}
        self.tca = tca
        self.config = tca.config
        self.is_active = True
        # Target correlation module
        self.tcm = TargetCorrelationModule(self)
        # Target Discimination Module
        self.tdm = TargetDisciminationModule(self)
        # Target Track Module
        self.ttm = TargetTrackModule(self)

    def process(self):
        """Filters all detections from the image processors through the Target
        Discrimination Module and the Target Correlation Module. The resulting
        finalized position list is then provided to the Target Track Module
        for track assignment and updating.

        NOTE: The is_active attribute must be True for processing to occur.

        Args:
            None
        """
        # Only process if active
        if not self.is_active:
            return

        for image_processor in self.tca.image_processors:
            # Only process if calibrated
            if not image_processor.cal_data.is_valid:
                continue

            # Discriminate positions
            self.tdm.discriminate(image_processor.last_detected_positions,
                                  image_processor)

        # Filter position list to obtain only unique targets
        unique_positions = self.tcm.checkUnique(self.tca.image_processors)

        logging.debug("-" * 20)
        logging.debug("UNIQUE POSITIONS: %s" % unique_positions)

        # Store finalized list of targets and assign/update tracks
        self.ttm.processDetections(unique_positions)

        # TODO Clean reference up
        self.targets = self.ttm.targets
        # TODO remove
        for target in self.ttm.targets:
            logging.debug("TARGET: %s" % target)

    def clearTargetData(self):
        """Erases all stored target data.

        Args:
            None
        """
        del self.ttm.targets[:]
        del self.targets[:]

    def toggleActive(self):
        """A boolean indicator that toggles the activity status of the data
        processor.

        Args:
            None
        """
        self.is_active = not self.is_active


def distance(p1, p2):
    """Calculates the distance between a pair of 2-D coordinates.

    Args:
        p1: A 2-D coordinate.
        p2: A 2-D coordinate.

    Returns:
        A float.
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def undistortImage(imageProc, image):
    """Removes distortion from image by applying intrinsic matrix and
    distortion coefficients.

    Note: ImageProcessor must have intrinsic parameters already loaded.

    Args:
        imageProc: An ImageProcessor object.
        image: A distorted 8-bit image array.

    Returns:
        An undistorted 8-bit image array.
    """
    return cv2.remap(image, imageProc.map1, imageProc.map2, cv2.INTER_LINEAR)


def convertToGlobal(imageProc, coordinates):
    """Converts a 2-D image coordinate to a 2-D global coordinate, according
    to calibration parameters.

    Args:
        imageProc: An ImageProcessor object.
        coordinates: A 2-D image coordinate.

    Returns:
        A 2-D global coordinate.
    """
    # Convert to numpy array
    coordinates = np.array(coordinates)

    imgPoint = np.ones((3, 1), np.float32)
    imgPoint[0, 0] = coordinates[0]
    imgPoint[1, 0] = coordinates[1]

    # Convert to matrix to simplify the following linear algebra
    imgPoint = np.matrix(imgPoint)
    intrinsic = np.matrix(imageProc.cal_data.intrinsic)
    rotation = np.matrix(imageProc.cal_data.rotation)
    translation = np.matrix(imageProc.cal_data.translation)

    leftMat = np.linalg.inv(rotation) * np.linalg.inv(intrinsic) * imgPoint
    rightMat = np.linalg.inv(rotation) * translation
    s = rightMat[2, 0]
    s /= leftMat[2, 0]

    position = np.array(np.linalg.inv(rotation)*(s * np.linalg.inv(intrinsic)
                                               * imgPoint - translation))[:2]

    # Convert from numpy to list
    from display.tactical.tactical import flattenArray
    position = flattenArray(position.tolist())

    return position
