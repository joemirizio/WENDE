import math
import logging
from collections import deque

from target import Target
from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE

class TargetTrackModule(object):
    
    KNOWN_GATE = 1.0
    UNKNOWN_GATE = 1.5
    CONSTANTS_SET = False
    
    def __init__(self, dataProcessor):
        self.targets = []
        self.config = dataProcessor.config
        if (TargetTrackModule.CONSTANTS_SET is False and
            self.config is not None):
            TargetTrackModule.CONSTANTS_SET = True
            TargetTrackModule.KNOWN_GATE = self.config.getfloat('track', 'known_gate')
            TargetTrackModule.UNKNOWN_GATE = self.config.getfloat('track', 'unknown_gate')

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.targets.append(Target(pos, self.config))

    def associateTrack(self, pos):
        for target in self.targets:
            if (target.prediction and 
                distance(pos, target.prediction) < TargetTrackModule.KNOWN_GATE):
                #logging.debug('Det associated: %f from prediction of target %d' %
                            # (distance(pos, target.prediction), i))
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
        return False

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
