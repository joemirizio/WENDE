import itertools
import math
import numpy as np


class CorrelationModule(object):
    def __init__(self, image_processor):
        self.image_processor = image_processor
    
    def checkUnique(self, img_processors, encloseTarg):
        # Return if calibration is not completed
        for proc in img_processors:
            if not proc.cal_data:
                return

        uniqueTarg = [] 
        proc1Points = []
        proc2Points = []
        
        # Create 2-element permutations of all image processors
        imgProcPermutations = list(itertools.permutations(encloseTarg, 2))
        
        # Remove all  reverse order permutations, i.e. remove BA if AB exists  
        for i, _ in enumerate(imgProcPermutations):
            reverseOrder = (imgProcPermutations[i][1], imgProcPermutations[i][0])
            for entry in imgProcPermutations:
                if entry == reverseOrder:
                      imgProcPermutations.remove(reverseOrder)

        # Convert all points in image proc pair to global coordinates
        for imgProcPair in imgProcPermutations:
            # Cycle through each coordinate in the first image processor 
            for point in imgProcPair[0]:
                point = np.array(point)
                point = convertToGlobal(img_processors[0], point)
                point = point.tolist()
                point = list(itertools.chain.from_iterable(point))
                proc1Points.append(point)
                uniqueTarg.append(tuple(point))
            # Cycle through each coordinate in the second image processor
            for point in imgProcPair[1]:
                point = np.array(point)
                point = convertToGlobal(img_processors[1], point)
                point = point.tolist()
                point = list(itertools.chain.from_iterable(point))
                proc2Points.append(point)
                uniqueTarg.append(tuple(point))
            # Create 2-element permutations of global coordinates 
            posPermutations = list(itertools.product(proc1Points, proc2Points))
            # Checks for adjacent targets and avgs their position if close
            for i, gblPointPair in enumerate(posPermutations):
                gblPoint1 = gblPointPair[0]
                gblPoint2 = gblPointPair[1]
                if distance(gblPoint1, gblPoint2) < 1:
                    uniqueTarg.append(tuple(np.mean((gblPoint1, gblPoint2), axis = 0)))
                    uniqueTarg.remove(tuple(gblPoint1))
                    uniqueTarg.remove(tuple(gblPoint2))
            # Removes duplicate points from detection list  
            uniqueTarg = list(set(uniqueTarg))
        return uniqueTarg
       
def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def convertToGlobal(imageProc, coordinates):
    """ Converts x and y coordinates to global coordinates, according to calibration parameters
    
    Arguments:
        imageProc -- ImageProcessor object
        coordinates -- x and y coordinates of input point in an array-like object
        
    Returns a 3D point in with coordinates in an array

    """
    
    imgPoint = np.ones( (3, 1), np.float32 )
    imgPoint[0, 0] = coordinates[0]
    imgPoint[1, 0] = coordinates[1]
    
    # Convert to matrix to simplify the following linear algebra
    # TODO: CLEAN THIS UP
    imgPoint = np.matrix(imgPoint)
    intrinsic = np.matrix(imageProc.cal_data.intrinsic)
    rotation = np.matrix(imageProc.cal_data.rotation)
    translation = np.matrix(imageProc.cal_data.translation)
    
    leftMat = np.linalg.inv(rotation) * np.linalg.inv(intrinsic) * imgPoint
    rightMat = np.linalg.inv(rotation) * translation
    s = rightMat[2,0]
    s /= leftMat[2,0]
    
    position = np.array(np.linalg.inv(rotation) * 
        (s * np.linalg.inv(intrinsic) * imgPoint - translation))[:2]
    return position
