import math
import logging
from collections import deque

from target import Target
from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE

KNOWN_GATE = 1.0 # for use after at least two detections (known vel)
UNKNOWN_GATE = 1.5  # for use after only one detection (unkown vel)

class TargetTrackModule(object):
    def __init__(self, dataProcessor):
        self.targets = []
        self.config = dataProcessor.config

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.targets.append(Target(pos, self.config))

    def associateTrack(self, pos):
        for target in self.targets:
            if (target.prediction and 
                distance(pos, target.prediction) < KNOWN_GATE):
                #logging.debug('Det associated: %f from prediction of target %d' %
                            # (distance(pos, target.prediction), i))
                target.update(pos)
                if target.missed_updates > 0:
                    target.missed_updates -= 1
                return True
            elif (not target.prediction and
                    distance(pos, target.pos) < UNKNOWN_GATE):
                target.prediction = []
                target.update(pos)
                if target.missed_updates > 0:
                    target.missed_updates -= 1
                return True

        # Got through the whole target list without a hit
        #logging.debug('Det NOT associated')
        return False

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)