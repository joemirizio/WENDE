"""
Defines a target object assigned to each validated detection.

Classes:
    Target

Functions:
    VerifyValidity()
    angle_diff()
    magnitude()
"""
import cv2.cv as cv
import logging
import math
from datetime import datetime
from collections import deque

from display.tactical.tactical import PERSIST_TIME, MAXLEN_DEQUE
import prediction

ORIGIN = [0, 0]


class Target(object):
    """Represents a single tracked object (i.e. a child).
    Keeps track of filter and position information.

    Attributes:
        pos: A 2-D position coordinate.
        id_value: An integer that identifies a single target object.
        ttm: A TargetTrackModule object.
        kalman: Instance of kalman filter tied to this target.
        prediction: A two element list of filter prediction values.
        missed_updates: An integer that records the number of missed track
            updates.
        filtered_positions: A list of positions after they've been processed
            by the kalman filter. Used for prediction.
        kal_meas: A 2x1 matrix containing the X and Y coordinates of the
            current target position.
        kal_pred: A 2x1 matrix containint the X and Y coordinates of the most
            recent prediction point.
        valid: A boolean indicating whether the position is within the safe
            zone radius.
        last_update: Used to expire old track data.
        predLineIntersect: A two element list containing the X, Y coordinate
            of the prediction line intersection point.
        predLineIntersectInitial: A two element list containing the X, Y
            coordinate of the initial predicted intersection point.
        updatedThisCycle: A boolean indicating whether the update method has
            completed running this cycle.
        first_turn: A boolean indicating whether a target has completed its
            first turn.
        second_turn: A boolean indicating whether a target has completed its
            second turn.
        max_velocity: Recorded maximum velocity since last turn; used to
            compare angle against to detect turns.
        left_safe: A boolean that indicates if the target has left the safe
            zone.
        left_alert: A boolean that indicates if the target has left the alert
            zone.
        prediction_positions: A queue containing the most recent predicted
            intersection points.

    Methods:
        update()
        clearTargetData()
        clearProcessedThisCycle()
        __repr__()
        makeKalman()
    """
    CONSTANTS_SET = False
    PROCESS_NOISE = 1
    MEASUREMENT_NOISE = 1e3
    TIME_STEP = 0.1
    PREDICTION_RADIUS = 12
    SAFE_RADIUS = 5
    TURN_THRESHOLD_DEGREES = 4
    NUM_PREDICTION_VALS = 20
    ID = 0

    def __init__(self, pos, config=None, ttm=None):
        self.pos = pos
        self.id_value = None
        self.ttm = ttm
        self.kalman = None
        self.prediction = None
        self.missed_updates = 0
        self.filtered_positions = deque([pos], maxlen=MAXLEN_DEQUE)
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
        self.hit_predict = None
        if Target.CONSTANTS_SET is False and config is not None:
            logging.debug('Setting track constants')
            Target.CONSTANTS_SET = True
            Target.PROCESS_NOISE = config.getfloat('track', 'process_noise')
            Target.MEASUREMENT_NOISE = config.getfloat('track',
                                                       'measurement_noise')
            Target.TIME_STEP = config.getfloat('track', 'time_step')
            Target.PREDICTION_RADIUS = config.getfloat('track',
                                                       'prediction_radius')
            Target.TURN_THRESHOLD_DEGREES = config.getfloat('track',
                                                            'turn_threshold')
            Target.NUM_PREDICTION_VALS = config. \
                getfloat('track', 'prediction_history_count')
            zone_distances = self.ttm.data_processor.tca.image_processors[0]. \
                scm.getCalibrationDistances()
            Target.PREDICTION_RADIUS = zone_distances[2]
            Target.SAFE_RADIUS = zone_distances[0]
        self.prediction_positions = deque([pos],
                                          maxlen=Target.NUM_PREDICTION_VALS)

        self.id_value = Target.ID
        Target.ID += 1

    def update(self, pos):
        """
        Update this target object with a position that it
        is known to be associated with. Association occurs
        before calling this.

        Args:
            pos: A two element list containing the X and Y value of a position
                known to be associated with this target.

        Returns:
            None
        """

        from data import distance

        self.pos = pos[0:2]
        #self.detected_positions.append(self.pos)
        self.missed_updates = 0

        if self.kalman is None:
            self.kalman = self.makeKalman(pos)

        self.kal_meas[0, 0] = pos[0]
        self.kal_meas[1, 0] = pos[1]
        # TODO Implement newer OpenCV Kalman functions
        tmp = cv.KalmanCorrect(self.kalman, self.kal_meas)
        if math.isnan(tmp[0, 0]):
            logging.error('Kalman correct returned nan')

        velocity = (tmp[2, 0], tmp[3, 0])
        if magnitude(velocity) > magnitude(self.max_velocity):
            self.max_velocity = velocity[:]

        #logging.debug('velocity: %f' % velocity)

        self.filtered_positions.append([tmp[0, 0], tmp[1, 0]])
        self.prediction_positions.append([tmp[0, 0], tmp[1, 0]])

        self.kal_pred = cv.KalmanPredict(self.kalman)
        self.prediction = [self.kal_pred[0, 0], self.kal_pred[1, 0]]

        zone_distances = self.ttm.data_processor.tca.image_processors[0].scm. \
            getCalibrationDistances()
        Target.PREDICTION_RADIUS = zone_distances[2]
        Target.SAFE_RADIUS = zone_distances[0]

        if self.valid:
            # Calculate prediction line when target is located in alert zone
            if (distance(self.pos, ORIGIN) > zone_distances[0] and
                    distance(self.pos, ORIGIN) < zone_distances[1]):
                self.predLineIntersect = prediction. \
                    predict(self.prediction_positions,
                            Target.PREDICTION_RADIUS,
                            Target.NUM_PREDICTION_VALS)
                if not self.predLineIntersectInitial and self.predLineIntersect:
                    self.predLineIntersectInitial = self.predLineIntersect[:]

        # check for turn
        if (len(self.prediction_positions) > zone_distances[1]
            and magnitude(self.max_velocity) > 0.0
            and math.fabs(angle_diff(self.max_velocity, velocity)) >
                Target.TURN_THRESHOLD_DEGREES):
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
            else:  # second turn
                self.second_turn = True
                logging.debug('SECOND TURN DETECTED')
                self.kalman = self.makeKalman(pos)

        # Update last time modified
        self.last_update = datetime.now()
        self.updatedThisCycle = True

    def clearTargetData(self):
        """
        Clear position lists associated with this target

        Args:
            None
        """
        #del self.detected_positions[:]
        self.filtered_positions.clear()
        self.prediction_positions.clear()
        del self.prediction[:]

    def clearProcessedThisCycle(self):
        """
        Toggle "updatedThisCycle" boolean to false if true.

        Args:
            None
        """
        if self.updatedThisCycle:
            self.updatedThisCycle = False

    def __repr__(self):
        """
        Returns 2-D position coordinate of target.

        Args:
            None
        """
        return "Target{(%f, %f)}" % (self.pos[0], self.pos[1])

    def makeKalman(self, pos, x_dot_init=0, y_dot_init=0):
        """
        Create new kalman filter based on single position and
        optionally a known velocity

        Args:
            pos: two element list containing X and Y coordinates
                of targets initial position
            x_dot_init: (optional) X coordinate of initial velocity
            y_dot_init: (optional) y coordinate of initial velocity

        Returns:
            instance of cv2 kalman filter
        """

        logging.debug('Creating new kalman instance')
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
        cv.SetIdentity(kalman.process_noise_cov,
                       cv.RealScalar(Target.PROCESS_NOISE))
        cv.SetIdentity(kalman.measurement_noise_cov,
                       cv.RealScalar(Target.MEASUREMENT_NOISE))
        cv.SetIdentity(kalman.error_cov_post, cv.RealScalar(1))

        return kalman


# This function is called during init to determine if a track is a running dog
def VerifyValidity(pos):
    """
    Check if a given position is within the radius of the safe zone

    Args:
        pos: two element list containing X and Y coordinates of
            position of interest

    Returns:
        Boolean indicating whether the position is within
        the safe zone radius
    """

    from processors.data import distance

    return distance(pos, ORIGIN) < Target.SAFE_RADIUS


def angle_diff(a, b):
    """
    Takes two cartesian points on a circle and
    returns the angular difference in degrees

    Args:
        a, b: two element lists containing X and
            Y coordinates of points on a circle with
            center 0,0

    Returns:
        Angular difference between the two points in degrees
    """

    radius_a = math.sqrt(a[0]**2 + a[1]**2)
    radius_b = math.sqrt(b[0]**2 + b[1]**2)
    ang_a = (180.0 / math.pi) * math.acos(a[0] / radius_a)
    ang_b = (180.0 / math.pi) * math.acos(b[0] / radius_b)
    #logging.debug('a: %1.20f\tb: %1.20f' % (ang_a, ang_b))
    return ang_b - ang_a


def magnitude(vector):
    """
    Returns the magnitude of a two dimensional vector
    represented as a two element list.

    Args:
        vector - two element list representing coordinates
            of a vector

    Returns:
        Magnitude of the vector
    """

    if vector is None or len(vector) is not 2:
        return None
    return math.sqrt(vector[0]**2 + vector[1]**2)
