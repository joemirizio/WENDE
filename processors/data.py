import cv2 as cv
import math
import logging
from track_list import TrackList

from target import Target

AREA_THRESHOLD = 200
DETECT_THRESHOLD = 0.75
TRACK_THRESHOLD = 0.075
POS_THRESHOLD = 0.05


class DataProcessor(object):
    def __init__(self):
        self.targets = []
        self.coverages = {}
        self.track_list = TrackList()

    def process(self, data, img_proc):
        for contour in data:
            area = cv.contourArea(contour)
            if area > AREA_THRESHOLD:
                center, radius = cv.minEnclosingCircle(contour)
                # Compute offset
                y = float(center[1]) / float(img_proc.img_source.height) * img_proc.coverage_size[1] 
                y = img_proc.A + (img_proc.B * y) + (img_proc.C * y**2)
                pos = ([float(center[0]) / float(img_proc.img_source.width) * img_proc.coverage_size[0] - (img_proc.coverage_size[0] / 2) + img_proc.coverage_offset[0],
                        img_proc.coverage_size[1] - y + img_proc.coverage_offset[1]])

                self.track_list.processDetection(pos)
                self.targets = self.track_list.tracks
        self.addCoverage(img_proc)

    # the following function no longer gets called. Detection association
    #   is now done in track_list.py
    def addTarget(self, target):
        isPresent = False
        for tgt in self.targets:
            dist = distance(target.pos, tgt.pos)
            if dist < DETECT_THRESHOLD:
                isPresent = True
                if dist > TRACK_THRESHOLD:
                    tgt.recordPosition()
                if dist > POS_THRESHOLD:
                    tgt.pos = target.pos
        if not isPresent:
            #logging.info("Adding target")
            self.targets.append(target)

    def addCoverage(self, img_proc):
        self.coverages[img_proc] = [img_proc.coverage_size, img_proc.coverage_offset]

    def clearTargetData(self):
        self.targets = []


def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

from random import random
import pdb
if __name__ == '__main__':
    tl = TrackList()
    data = [[i+random()-0.5, i+random()-0.5] for i in range(100)]
    for pos in data:
        #pdb.set_trace()
        tl.processDetection(pos)
