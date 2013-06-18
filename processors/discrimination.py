import math
import cv2
import numpy as np
import logging
import data

MIN_AREA_THRESHOLD = 100
MAX_AREA_THRESHOLD = 7500

ORIGIN = [0,0]

class TargetDisciminationModule(object):

    def __init__(self):
        self.validTargets = []
                                                      
    def discriminate(self, contour_data, img_process):
        
        for contour in contour_data:
            area = cv2.contourArea(contour)
            # Checks for acceptable contour area
            if area > MIN_AREA_THRESHOLD and area < MAX_AREA_THRESHOLD:
                center, radius = cv2.minEnclosingCircle(contour)
                pos = self.data.convertToGlobal(img_process, center)
                # Checks to see if object is within the demo area boundaries 
                if distance(pos, ORIGIN) <= 12 and math.fabs(pos[0])*math.tan(0.5236) < math.fabs(pos[1]): 
                    # Calculate expected target contour area based on distance from camera
                    expected_contour = 1903*math.pow(distance(pos, ORIGIN),-0.861) 
                    upper_area_ = 1.8*expected_contour
                    lower_area = 0.5*expected_contour
                    # Add to target list if size conditions satisfied
                    if area > lower_area and area < upper_area:
                        self.validTargets.append(pos)
                        logging.debug("Target Detection: %s" % pos)
                
        return (self.validTargets)
    
    def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)