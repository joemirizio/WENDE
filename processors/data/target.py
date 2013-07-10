import cv2.cv as cv
import logging
import math
from datetime import datetime
from collections import deque

from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE
import prediction

ORIGIN = [0, 0]

class Target(object):
    
    CONSTANTS_SET = False
    PROCESS_NOISE = 1
    MEASUREMENT_NOISE = 1e3
    TIME_STEP = 0.1
    PREDICTION_RADIUS = 12
    TURN_THRESHOLD_DEGREES = 4
    
    def __init__(self, pos, config=None):
        self.pos = pos
        self.kalman = None
        self.prediction = None
        self.missed_updates = 0
        #self.detected_positions = [pos]
        self.filtered_positions = deque([pos], maxlen=MAXLEN_DEQUE)
        self.prediction_positions = deque([pos], maxlen=prediction.NUM_PREDICTION_VALS)
        self.kal_meas = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.kal_pred = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.valid = VerifyValidity(pos)
        self.last_update = datetime.now()
        self.predLineIntersect = None
        self.predLineIntersectInitial = None
        self.updatedThisCycle = True
        self.first_turn = False
        self.second_turn = False
        self.max_velocity = None
        self.left_safe = None
        self.left_alert = None
        if Target.CONSTANTS_SET is False and config is not None:
            logging.debug('Setting track constants')
            Target.CONSTANTS_SET = True
            Target.PROCESS_NOISE = config.getfloat('track', 'process_noise')
            Target.MEASUREMENT_NOISE = config.getfloat('track', 'measurement_noise')
            Target.TIME_STEP = config.getfloat('track', 'time_step')
            Target.PREDICTION_RADIUS = config.getfloat('track', 'prediction_radius')
            Target.TURN_THRESHOLD_DEGREES = config.getfloat('track', 'turn_threshold')

    def update(self, pos):
        # TODO Reimplement
        if self.updatedThisCycle:
            return

        self.pos = pos[0:2]
        #self.detected_positions.append(self.pos)
        self.missed_updates = 0

        if self.kalman is None:
            self.kalman = self.makeKalman(pos)

        self.kal_meas[0, 0] = pos[0]
        self.kal_meas[1, 0] = pos[1]
        # TODO Implement newer OpenCV Kalman functions
        tmp = cv.KalmanCorrect(self.kalman, self.kal_meas)
        
        velocity = (tmp[2, 0], tmp[3, 0])
        if magnitude(velocity) > magnitude(self.max_velocity):
            self.max_velocity = velocity[:]
        
        #logging.debug('velocity: %f' % velocity)

        self.filtered_positions.append([tmp[0, 0], tmp[1, 0]])
        self.prediction_positions.append([tmp[0, 0], tmp[1, 0]])

        self.kal_pred = cv.KalmanPredict(self.kalman)
        self.prediction = [self.kal_pred[0, 0], self.kal_pred[1, 0]] 

        if self.valid:
            # Calculate prediction line when target is located in alert zone
            if distance(self.pos, ORIGIN) > 5 and distance(self.pos, ORIGIN) < 10:
                self.predLineIntersect = prediction.predict(self.prediction_positions, Target.PREDICTION_RADIUS)
                if not self.predLineIntersectInitial and self.predLineIntersect:
                    self.predLineIntersectInitial = self.predLineIntersect[:]
               
        # check for turn
        if (len(self.prediction_positions) > 10
            and magnitude(self.max_velocity) > 0.0
            and math.fabs(angle_diff(self.max_velocity, velocity)) > Target.TURN_THRESHOLD_DEGREES):
            self.max_velocity = None
            self.prediction_positions.clear()
            self.predLineIntersectInitial = None
            self.predLineIntersect = None
            #TODO initialize new kalman with appropriate velocity
            #    i.e. ninety degrees from self.max_velocity
            if self.first_turn is False:
                self.first_turn = True
                logging.debug('FIRST TURN DETECTED')
                self.kalman = self.makeKalman(pos)
            else: # second turn
                self.second_turn = True
                logging.debug('SECOND TURN DETECTED')
                self.kalman = self.makeKalman(pos)

        # Update last time modified
        self.last_update = datetime.now()
        self.updatedThisCycle = True

    def clearTargetData(self):
        #del self.detected_positions[:]
        self.filtered_positions.clear()
        self.prediction_positions.clear()
        del self.prediction[:]
    
    def clearProcessedThisCycle(self):
        if self.updatedThisCycle:
            self.updatedThisCycle = False

    def __repr__(self):
        return "Target{(%f, %f)}" % (self.pos[0], self.pos[1])
    
    #This function takes in the target position and returns a kalman filter
    def makeKalman(self, pos, x_dot_init=0, y_dot_init=0):
        kalman = cv.CreateKalman(dynam_params=4, measure_params=2)
    
        # Set previous state prediction
        x_init = pos[0]
        y_init = pos[1]
        kalman.state_pre[0, 0] = x_init
        kalman.state_pre[1, 0] = y_init
        kalman.state_pre[2, 0] = x_dot_init
        kalman.state_pre[3, 0] = y_dot_init
    
        tk = Target.TIME_STEP
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
        cv.SetIdentity(kalman.process_noise_cov, cv.RealScalar(Target.PROCESS_NOISE))
        cv.SetIdentity(kalman.measurement_noise_cov, cv.RealScalar(Target.MEASUREMENT_NOISE))
        cv.SetIdentity(kalman.error_cov_post, cv.RealScalar(1))
    
        return kalman

# This function is called during init to determine if a track is a running dog
def VerifyValidity(pos):
    return distance(pos, ORIGIN) < 5


#This function computes the distance between two points
def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


    

def angle_diff(a, b):
    # given two cartesian points on a circle
    # return the angular difference in degrees
    radius_a = math.sqrt(a[0]**2 + a[1]**2)
    radius_b = math.sqrt(b[0]**2 + b[1]**2)
    ang_a = (180.0 / math.pi) * math.acos(a[0] / radius_a)
    ang_b = (180.0 / math.pi) * math.acos(b[0] / radius_b)
    #logging.debug('a: %1.20f\tb: %1.20f' % (ang_a, ang_b))
    return ang_b - ang_a
    
def magnitude(vector):
    if vector is None or len(vector) is not 2:
        return None
    return math.sqrt(vector[0]**2 + vector[1]**2)

