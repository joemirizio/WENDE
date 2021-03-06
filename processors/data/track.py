#!/usr/bin/python
"""
The target track module represents a compilation of three components in the
original design: the target track module, the target location module, and
the target prediction module. This module maintains individual tracks through
a list of target objects.

Classes:
    TargetTrackModule

Functions:
    distance()
"""
import math
import logging
from collections import deque

from target import Target
from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE


class TargetTrackModule(object):
    """
    The target track module represents a compilation of three components in
    the original design: the target track module, the target location module,
    and the target prediction module. This module associates tracks to moving
    targets and maintains individual tracks through a list of target objects.

    Attributes:
        targets: A list of Target objects.
        data_processor: A DataProcessor object.
        config: A SafeConfigParser object.

    Methods:
        processDetections()
        associateTrack()
    """
    KNOWN_GATE = 1.0
    UNKNOWN_GATE = 1.5
    CONSTANTS_SET = False

    def __init__(self, data_processor):
        self.targets = []
        self.data_processor = data_processor
        self.config = data_processor.config
        if (TargetTrackModule.CONSTANTS_SET is False and
                self.config is not None):
            TargetTrackModule.CONSTANTS_SET = True
            TargetTrackModule.KNOWN_GATE = self.config.getfloat('track',
                                                                'known_gate')
            TargetTrackModule.UNKNOWN_GATE = self.config. \
                getfloat('track', 'unknown_gate')

    def processDetections(self, unmatchedList):
        """
        This method takes in a list of unique tracks from the target
        discrimination module. These points are the results of matching all the
        detections from the various image processors compiled into a unique
        list. This does a first fit match for detected points and existing
        targets. Initially the program tries to only allow a single point to
        modify one target. After all points have been exhausted they may be
        used again. This handles merging and splitting. Any leftover points are
        marked as new targets.

        Args:
            unmatchedList: A list of 2-D position coordinates for valid
                targets.
        """
        matchedList = []
        for target in self.targets:
            associated = False
            logging.debug("--current target--")
            logging.debug(target)
            logging.debug("--unmatched list--")
            logging.debug(unmatchedList)
            logging.debug("--matched list--")
            logging.debug(matchedList)
            for i in xrange(len(unmatchedList) - 1, -1, -1):
                pos = unmatchedList[i]
                logging.debug("-curret pos-")
                logging.debug(pos)
                associated = self.associateTrack(pos, target)

                if associated:
                    logging.debug("Target Associated!")
                    matchedList.append(pos)
                    del unmatchedList[i]
                    break

                logging.debug("Target Not Associated")
            if not associated:
                for pos in matchedList:
                    associated = self.associateTrack(pos, target)

        for pos in unmatchedList:
            logging.debug("New Target:")
            logging.debug(pos)
            self.targets.append(Target(pos, self.config, self))

    def associateTrack(self, pos, target):
        """
        Compare a position to known targets and try to
        associate it to one of them.

        Args:
            pos: A two element list representing the X and Y
                of a position
            Targets: A list of known targets represented as
                Target objects

        Returns:
            A boolean indicating whether the given position
            was associated with any of the known targets
        """

        if target.updatedThisCycle:
            logging.debug("already associated")
            return False

        logging.debug("target prediction")
        logging.debug(target.prediction)
        if (target.prediction and
                distance(pos, target.prediction) <
                TargetTrackModule.KNOWN_GATE):
            #logging.debug('Det associated: %f frm predict of target %d'%)
            #             (distance(pos, target.prediction), i))
            logging.debug('Det associated: %f from predictian of target '
                          % (distance(pos, target.prediction)))
            target.update(pos)
            if target.missed_updates > 0:
                target.missed_updates -= 1
            return True
        elif (not target.prediction and
                distance(pos, target.pos) < TargetTrackModule.UNKNOWN_GATE):
            target.prediction = []
            target.update(pos)
            if target.missed_updates > 0:
                target.missed_updates -= 1
            return True

        # Got through the whole target list without a hit
        #logging.debug('Det NOT associated'))
        return False


def distance(p1, p2):
    """Calculates the distance between a pair of 2-D coordinates.

    Args:
        p1: A 2-D coordinate.
        p2: A 2-D coordinate.

    Returns:
        A float.
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# if __name__ == '__main__':
#     track = TargetTrackModule(0)
#     for q in range(10000):
#         x1 = .001*(q-5000)
#         y1 = x1+7
#         x2 = -x1
#         y2 = -x2+7
#         if distance([x1,y1],[x2,y2]) < .6:
#             unmatchedList = [[x1,y1]]
#         else:
#             unmatchedList = [[x1,y1],[x2,y2]]
#         print"----------------------------------New Targets----------------"
#         print unmatchedList
#         track.processDetections(unmatchedList)
#         for target1 in track.targets:
#             if target1.updatedThisCycle:
#                 target1.updatedThisCycle = False
#             print target1
