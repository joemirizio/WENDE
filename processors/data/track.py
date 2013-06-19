import math
import logging
from collections import deque

from target import Target
from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE

KNOWN_GATE = 0.8  # for use after at least two detections (known vel)
UNKNOWN_GATE = 0.5  # for use after only one detection (unkown vel)
MAXED_MISSED_UPDATES = 2

class TargetTrackModule(object):
    def __init__(self, dataProcessor):
        self.targets = []

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.targets.append(Target(pos))
        for target in self.targets:
            target.clearProcessedThisCycle()

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
    
    def incrementUpdateCount(self):
        for target in self.targets:
            target.missed_updates += 1
            
    def clearStaleTargets(self):
        for target in self.targets:
            if target.missed_updates > MAX_MISSED_UPDATES:
                logging.debug('Dropping track due to missed updates')
                self.targets.remove(target)

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
