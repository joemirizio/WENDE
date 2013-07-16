from numpy.linalg import lstsq
import numpy as np
from math import sqrt
from random import random
import itertools

# Predict:
#   predict intersection point with track and prediction line
#   given previous detection coordinates and radius of the
#   detection line
#
#   det_coords:
#       List of two element lists representing coordinates.
#       e.g. [[x1, y1], [x2, y2], ...]
#       This will need to be edited after refactoring to point class.
#   pred_line_r:
#       Radius of the prediction line from the origin.
#       Should be in same units as x and y (i.e. meters)

def predict(positions, pred_line_r, num_prediction_vals):
    """
    Predict intersection point with track and prediction line
    given previous detection coordinates and radius of the
    detection line.
    
    Args:
        positions - List of two dimensional target positions
            to predict from
        pred_line_r - Radius of the prediction line
        num_prediction_vals - minimum number of values to 
            return a valid prediction
            
    Returns:
        Two element list containing the X and Y coordinate of the
            predicted crossing point of the prediction line
    """

    # Prevent prediction when insufficient data is provided
    if len(positions) < num_prediction_vals:
        return None

    # Restrict to the maximum number of prediction values
#     if len(positions) > NUM_PREDICTION_VALS:
#         positions = list(itertools.islice(
#             positions, (len(positions) - NUM_PREDICTION_VALS), None))

    # reformat into x and y arrays
    x = [pair[0] for pair in positions]
    y = [pair[1] for pair in positions]

    # create blank slate to predict against
    A = np.vstack([x, np.ones(len(x))]).T

    # use numpy least squares function to get slope and intercept
    slope, y_incpt = lstsq(A, y)[0]

    # create a, b and c for quadratic equation to solve for x given:
    #   (y = slope * x + y_intcp)
    #       and
    #   (pred_line_r**2 = x**2 + y**2)
    a = 1 + slope**2
    b = 2 * slope * y_incpt
    c = y_incpt**2 - pred_line_r**2

    # Verify roots are not imaginary
    try:
        check_imaginary = sqrt(b**2 - 4*a*c)
    except:
        logging.error("Imaginary roots. Cannot predict location.")
        return

    x_pred = (-b + sqrt(b**2 - 4*a*c)) / (2*a)
    y_pred = slope * x_pred + y_incpt
    if y_pred > 0:
        return [x_pred, y_pred]

    x_pred = (-b - sqrt(b**2 - 4*a*c)) / (2*a)
    y_pred = slope * x_pred + y_incpt
    return [x_pred, y_pred]

if __name__ == '__main__':
    fake_dets = [[i + 2*random()-1, i + 2*random()-1] for i in range(100)]
    print predict(fake_dets, 100)
    # should get about (70.7, 70.7)
