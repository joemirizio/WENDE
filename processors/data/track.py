"""
The target track module represents a compilation of three components in the 
original design: the target track module, the target location module, and
the target prediction module. This module maintains individual tracks through
a list of target objects. 
"""
import math
import logging
from collections import deque

from target import Target
from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE

KNOWN_GATE = 1 # for use after at least two detections (known vel)
UNKNOWN_GATE = 1.5  # for use after only one detection (unkown vel)
MAXED_MISSED_UPDATES = 2

class TargetTrackModule(object):
    def __init__(self, dataProcessor):
        self.targets = []

    """
    This method takes in a list of unique tracks from the target discrimination
    module. These points are the results of matching all the detections from the
    various image processors compiled into a unique list. This does a first fit 
    match for detected points and existing targets. Initially the program tries
    to only allow a single point to modify one target. After all points have 
    been exhausted they may be used again. This handles merging and splitting.
    Any leftovr points are marked as new targets.
    """
    def processDetections(self, unmatchedList):
        matchedList = []
        for target in self.targets:
            associated = False
            for i in xrange(len(unmatchedList) - 1, -1, -1):
                pos = unmatchedList[i]
                associated = self.associateTrack(pos,target)
		if associated: 
                    matchedList.push(pos)
                    del unmatchedList[i]
                    break
             if not associated:
                 for pos in matchedList:
                     associated = self.associateTrack(pos,target)
            
        for pos in unmatchedList:
            self.targets.append(Target(pos))

    def associateTrack(self, pos, target):
        # TODO reimplement
        if target.updatedThisCycle:
            return False

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
