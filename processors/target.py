import cv2.cv as cv
import math

ORIGIN = [0, 0]
PROCESS_NOISE = 1e-2
MEASUREMENT_NOISE = 1

class Target(object):
    def __init__(self, pos):
        self.tracks = []
        self.pos = pos
        self.kalman = None
        self.prediction = None
        self.smooth_dets = [pos]
        self.kal_meas = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.kal_pred = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.valid = VerifyValidity(pos)

    def update(self, pos):
        # This statement is for compatibility with old drawing method only
        self.tracks.append(self.pos)

        if self.kalman is None:
            self.kalman = makeKalman(pos)

        self.pos = pos
        self.kal_meas[0, 0] = pos[0]
        self.kal_meas[1, 0] = pos[1]
        # TODO Implement newer OpenCV Kalman functions
        tmp = cv.KalmanCorrect(self.kalman, self.kal_meas)
        self.smooth_dets.append([tmp[0, 0], tmp[1, 0]])
        self.kal_pred = cv.KalmanPredict(self.kalman)
        self.prediction = [self.kal_pred[0, 0], self.kal_pred[1, 0]]
        #self.tracks = self.smooth_dets

    def __repr__(self):
        return "Target{(%f, %f)}" % (self.pos[0], self.pos[1])

# Not yet implemented, this function will be used when a new Target object is
# made and will determine if the tracked object is a "running dog" this happens
# in init since future positions don't matter, from I imagine when the display
# is drawing targets, it will first check their valididy before drawing them
def VerifyValidity(pos):
    output = False
    if distance(pos, ORIGIN) < 5:
        output = True
    return output


def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


# This is not supposed to be a member function of class target please don't indent
def makeKalman(pos):
    kalman = cv.CreateKalman(dynam_params=4, measure_params=2)

    # Set previous state prediction
    x_init = pos[0]
    y_init = pos[1]
    x_dot_init = 1
    y_dot_init = 1
    kalman.state_pre[0, 0] = x_init
    kalman.state_pre[1, 0] = y_init
    kalman.state_pre[2, 0] = x_dot_init
    kalman.state_pre[3, 0] = y_dot_init

    tk = 1
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
