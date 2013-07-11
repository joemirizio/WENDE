import itertools
import math
import numpy as np

class TargetCorrelationModule(object):
    def __init__(self, image_processor):
        self.image_processor = image_processor
    
    def checkUnique(self, image_processors):
        from data import distance
        #for proc in image_processors:
            # Return if calibration is not completed
            #if not proc.cal_data.is_valid:
                #return []

        #uniqueTarg = [] 
        #proc1Points = []
        #proc2Points = []
        
        ## Create 2-element permutations of all image processors
        #imgProcPermutations = list(itertools.permutations(positions, 2))
        
        ## Remove all  reverse order permutations, i.e. remove BA if AB exists  
        #for i, _ in enumerate(imgProcPermutations):
            #reverseOrder = (imgProcPermutations[i][1], imgProcPermutations[i][0])
            #for entry in imgProcPermutations:
                #if entry == reverseOrder:
                      #imgProcPermutations.remove(reverseOrder)

        ## Convert all points in image proc pair to global coordinates
        #for imgProcPair in imgProcPermutations:
            ## Cycle through each coordinate in the first image processor 
            #for point in imgProcPair[0]:
                #point = np.array(point)
                #point = convertToGlobal(image_processors[0], point)
                #point = point.tolist()
                #point = list(itertools.chain.from_iterable(point))
                #proc1Points.append(point)
                #uniqueTarg.append(tuple(point))
            ## Cycle through each coordinate in the second image processor
            #for point in imgProcPair[1]:
                #point = np.array(point)
                #point = convertToGlobal(image_processors[1], point)
                #point = point.tolist()
                #point = list(itertools.chain.from_iterable(point))
                #proc2Points.append(point)
                #uniqueTarg.append(tuple(point))
            ## Create 2-element permutations of global coordinates 
            #posPermutations = list(itertools.product(proc1Points, proc2Points))
            ## Checks for adjacent targets and avgs their position if close
            #for i, gblPointPair in enumerate(posPermutations):
                #gblPoint1 = gblPointPair[0]
                #gblPoint2 = gblPointPair[1]
                #if distance(gblPoint1, gblPoint2) < 1:
                    #uniqueTarg.append(tuple(np.mean((gblPoint1, gblPoint2), axis = 0)))
                    #uniqueTarg.remove(tuple(gblPoint1))
                    #uniqueTarg.remove(tuple(gblPoint2))
            ## Removes duplicate points from detection list  
            #uniqueTarg = list(set(uniqueTarg))

        unique_positions = []
        for image_processor in image_processors:
            #
            if image_processor.cal_data.is_valid:
                continue

            for position in image_processor.last_detected_positions:
                #
                position_matched = False
                for i, unique_position in enumerate(unique_positions):
                    #
                    if distance(position, unique_position) < 0.5:
                        unique_positions[i] = np.mean(position, unique_position)
                        position_matched = True
                        break
                #
                if not position_matched:
                    unique_positions.append(position)

        return unique_positions
