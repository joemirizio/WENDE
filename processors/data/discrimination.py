import math
import cv2
import numpy as np
import logging
import data

MIN_AREA_THRESHOLD = 100
MAX_AREA_THRESHOLD = 7500

ORIGIN = [0,0]

class TargetDisciminationModule(object):

    def __init__(self, data_processor):
        self.data_processor = data_processor
                                                      
    def discriminate(self, contour_data, image_processor):
        from data import distance
        from data import convertToGlobal
        from processors.image.calibration import SourceCalibrationModule

        valid_targets = []
        for contour in contour_data:
            # Check for acceptable contour area
            area = cv2.contourArea(contour)
            if area > MIN_AREA_THRESHOLD and area < MAX_AREA_THRESHOLD:
                # Check to see if object is within the demo area boundaries 
                center, radius = cv2.minEnclosingCircle(contour)
                pos = convertToGlobal(image_processor, center)
                position_in_demo_area = (math.fabs(pos[0]) * math.tan(0.5236) <
                                         math.fabs(pos[1]))
                
                # Limit the TCA to the zone boundary (with padding)
                max_zone_distance = SourceCalibrationModule.ZONE_DISTANCES[-1] + 0.25
                if distance(pos, ORIGIN) <= max_zone_distance and position_in_demo_area:
                    # Calculate expected target contour area based on distance from camera
                    expected_contour = 1903 * math.pow(distance(pos, ORIGIN), -0.861) 
                    upper_area = 1.8 * expected_contour
                    lower_area = 0.4 * expected_contour
                    # Add to target list if size conditions satisfied
                    if area > lower_area and area < upper_area:
                        valid_targets.append(pos)
                
        image_processor.valid_targets = valid_targets
        return valid_targets
