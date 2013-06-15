import math
import logging
from collections import deque

from target import Target
from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE

KNOWN_GATE = 2  # for use after at least two detections (known vel)
UNKNOWN_GATE = 1  # for use after only one detection (unkown vel)

class TrackList(object):
    def __init__(self):
        self.tracks = []

    def processDetection(self, pos):
        associated = self.associateTrack(pos)
        if not associated:
            self.tracks.append(Target(pos))

    def associateTrack(self, pos):
        for i, track in enumerate(self.tracks):
            if (track.prediction and 
                distance(pos, track.prediction[-1]) < KNOWN_GATE):
                #logging.debug('Det associated: %f from prediction of track %d' %
                            # (distance(pos, track.prediction), i))
                track.update(pos)
                return True
            elif (not track.prediction and
                    distance(pos, track.pos[-1]) < UNKNOWN_GATE):
                track.prediction = deque(maxlen=MAXLEN_DEQUE)
                track.update(pos)
                return True

        # Got through the whole track list without a hit
        #logging.debug('Det NOT associated')
        return False

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
