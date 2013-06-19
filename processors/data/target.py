import cv2.cv as cv
import logging
import math
from datetime import datetime
from collections import deque

from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE
import prediction

ORIGIN = [0, 0]
NUM_PREDICTION_VALS = 20

PROCESS_NOISE = 1e-1
MEASUREMENT_NOISE = 1
TIME_STEP = 0.5
PREDICTION_RADIUS = 12

class Target(object):
    def __init__(self, pos):
        self.pos = pos
        self.kalman = None
        self.prediction = None
        self.missed_updates = 0
        self.detected_positions = [pos]
        self.filtered_positions = deque([pos], maxlen=MAXLEN_DEQUE)
        self.kal_meas = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.kal_pred = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.valid = VerifyValidity(pos)
        self.last_update = datetime.now()
        self.predLineIntersect = ORIGIN
        self.beyond9 = False
        self.updatedThisCycle = True

    def update(self, pos):
        # TODO Reimplement
        if self.updatedThisCycle:
            return

        logging.debug('Updating %s' % self)
        self.pos = pos[0:2]
        self.detected_positions.append(self.pos)
        self.missed_updates = 0

        if self.kalman is None:
            self.kalman = makeKalman(pos)

        self.kal_meas[0, 0] = pos[0]
        self.kal_meas[1, 0] = pos[1]
        # TODO Implement newer OpenCV Kalman functions
        tmp = cv.KalmanCorrect(self.kalman, self.kal_meas)

        self.filtered_positions.append([tmp[0, 0], tmp[1, 0]])
        #logging.debug("Smoothed Detections: %s" % self.filtered_positions[-1])

        self.kal_pred = cv.KalmanPredict(self.kalman)
        self.prediction = [self.kal_pred[0, 0], self.kal_pred[1, 0]] 
        if self.valid:
            #if distance(self.pos, ORIGIN) > 9:
            self.beyond9 = True
            self.predLineIntersect = prediction.predict(
                self.detected_positions[-NUM_PREDICTION_VALS:], 
                PREDICTION_RADIUS)

        # Update last time modified
        self.last_update = datetime.now()
        self.updatedThisCycle = True

    def clearTargetData(self):
        del self.detected_positions[:]
        self.filtered_positions.clear()
        del self.prediction[:]
    
    def clearProcessedThisCycle(self):
        if self.updatedThisCycle:
            self.updatedThisCycle = False

    def __repr__(self):
        return "Target{(%f, %f)}" % (self.pos[0], self.pos[1])

# This function is called during init to determine if a track is a running dog
def VerifyValidity(pos):
    return distance(pos, ORIGIN) < 5


#This function computes the distance between two points
def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


#This function takes in the target position and returns a kalman filter
def makeKalman(pos):
    kalman = cv.CreateKalman(dynam_params=4, measure_params=2)

    # Set previous state prediction
    x_init = pos[0]
    y_init = pos[1]
    x_dot_init = 0
    y_dot_init = 0
    kalman.state_pre[0, 0] = x_init
    kalman.state_pre[1, 0] = y_init
    kalman.state_pre[2, 0] = x_dot_init
    kalman.state_pre[3, 0] = y_dot_init

    tk = TIME_STEP
    # Set kalman transition matrix
    kalman.transition_matrix[0, 0] = 1
    kalman.transition_matrix[0, 1] = 0
    kalman.transition_matrix[0, 2] = tk
    kalman.transition_matrix[0, 3] = 0
    kalman.transition_matrix[1, 0] = 0
    kalman.transition_matrix[1, 1] = 1
    kalman.transition_matrix[1, 2] = 0
    kalman.transition_matrix[1, 3] = tk
    kalman.transition_matrix[2, 0] = 0
    kalman.transition_matrix[2, 1] = 0
    kalman.transition_matrix[2, 2] = 1
    kalman.transition_matrix[2, 3] = 0
    kalman.transition_matrix[3, 0] = 0
    kalman.transition_matrix[3, 1] = 0
    kalman.transition_matrix[3, 2] = 0
    kalman.transition_matrix[3, 3] = 1

    # Set Kalman Filter
    cv.SetIdentity(kalman.measurement_matrix, cv.RealScalar(1))
    cv.SetIdentity(kalman.process_noise_cov, cv.RealScalar(PROCESS_NOISE))
    cv.SetIdentity(kalman.measurement_noise_cov, cv.RealScalar(MEASUREMENT_NOISE))
    cv.SetIdentity(kalman.error_cov_post, cv.RealScalar(1))

    return kalman
