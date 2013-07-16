"""
Analyzes detected targets from all system image processors and determines
whether identified targets are unique or reference the same object. For
instance, this functionality allows the system to recognize a target as a
single object even while viewed by multiple image sources simultaneously.

Classes:
TargetCorrelationModule
"""
import math
import numpy as np


class TargetCorrelationModule(object):
    """Analyzes detected targets from all system image processors and
    determines whether identified targets are unique or reference the same
    object. This is done by comparing their relative proximity.

    Attributes:
    image_processor: An ImageProcessor object.

    Methods:
    checkUnique()
    """
    def __init__(self, image_processor):
        self.image_processor = image_processor

    def checkUnique(self, image_processors):
        """Reads in one or more ImageProcessor objects and determines whether
        identified targets in these image processors are unique or reference
        the same object.

        Detections located within 0.5 feet of each other are assumed to
        reference the same object. In this case, the two target postions are
        averaged into a single coordinate and added to the unique positions
        list. The unique positions list stores the coordinates of all targets
        identified as unique across all image processors.

        Args:
            image_processors: A list of ImageProcessor objects.

        Returns:
            A list of 2-D coordinates.
        """

        from data import distance

        unique_positions = []
        for image_processor in image_processors:
            # Check for calibrated system condition
            if not image_processor.cal_data.is_valid:
                continue

            # Compare all valid targets, looking for closely adjacent pairs
            for position in image_processor.valid_targets:
                position_matched = False
                for i, unique_position in enumerate(unique_positions):
                    # Targets located within 0.5 feet of each other have their
                    # positions averaged into a single coordinate that is
                    # then added to the unique positions list
                    if distance(position, unique_position) < 0.5:
                        unique_positions[i] = np.mean((position,
                                                      unique_position), axis=0)
                        position_matched = True
                        break
                # Targets distanced from other targets have their coordinates
                # added to the unique positions list
                if not position_matched:
                    unique_positions.append(position)

        return unique_positions
