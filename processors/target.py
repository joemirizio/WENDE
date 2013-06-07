import cv2.cv as cv


class Target(object):
    def __init__(self, pos):
        self.pos = pos
        self.kalman = makeKalman(pos)
        self.prediction = pos
        self.smooth_dets = []
        self.kal_meas = cv.CreateMat(2, 1, cv.CV_32FC1)
        self.kal_pred = cv.CreateMat(2, 1, cv.CV_32FC1)
	self.valid = VerifyValidity(pos)

    def update(self, pos):
        self.kal_meas[0, 0] = pos[0]
        self.kal_meas[1, 0] = pos[1]
        self.smooth_dets.append(cv.KalmanCorrect(self.kalman, self.kal_meas))
        self.kal_pred = cv.KalmanPredict(self.kalman)
        self.prediction[0] = self.kal_pred[0, 0]  # x
        self.prediction[1] = self.kal_pred[1, 0]  # y

    def __repr__(self):
        return "Target{(%d, %d)}" % (self.pos[0], self.pos[1])

#Not yet implemented, this function will be used when a new Target object is 
#made and will determine if the tracked object is a "running dog" this happens
#in init since future positions don't matter, from I imagine when the display 
#is drawing targets, it will first check their valididy before drawing them
def VerifyValidity(pos):
    return True

#This is not supposed to be a member function of class target please don't indent
def makeKalman( position):
    kalman = cv.CreateKalman(dynam_params=4, measure_params=2)

    # set previous state prediction
    x_init = position[0]
    y_init = position[1]
    x_dot_init = 0
    y_dot_init = 0
    kalman.state_pre[0, 0] = x_init
    kalman.state_pre[1, 0] = y_init
    kalman.state_pre[2, 0] = x_dot_init
    kalman.state_pre[3, 0] = y_dot_init

    # set kalman transition matrix
    tk = 1
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

    # set Kalman Filter
    cv.SetIdentity(kalman.measurement_matrix, cv.RealScalar(1))
    cv.SetIdentity(kalman.process_noise_cov, cv.RealScalar(1e-5))
    cv.SetIdentity(kalman.measurement_noise_cov, cv.RealScalar(1e-1))
    cv.SetIdentity(kalman.error_cov_post, cv.RealScalar(1))

    return kalman

#if __name__ == '__main__':
    #TODO: UNIT TEST
#    return
