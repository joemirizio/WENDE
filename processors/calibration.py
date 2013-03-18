import cv2 as cv
import itertools as it
import logging

FLANN_INDEX_KDTREE = 1
FLANN_INDEX_LSH = 6

class Calibrator(object):

	def __init__(self, image_processors=None):
		self.calibrations = {}
		if image_processors:
			self.calibrateImageProcessors(image_processors)

	def calibrateImageProcessors(self, image_processors):
		for img_proc1, img_proc2 in it.combinations(image_processors, 2):
			self.calibrations[(img_proc1, img_proc2)] = calibrateImages(img_proc1, img_proc2)
		logging.info(repr(self.calibrations))

	def getCalibration(self, img_proc1, img_proc2=None):
		if not img_proc2:
			return [proc_comb for proc_comb in self.calibrations.iteritems() 
					if img_proc1 in proc_comb[0]]
		else:
			return [proc_comb[1] for proc_comb in self.calibrations.iteritems() 
					if img_proc1 in proc_comb[0] and img_proc2 in proc_comb[0]][0]


def calibrateImages(img1, img2):
	flann_params = dict(algorithm=FLANN_INDEX_LSH,
	                   table_number=6, # 12
	                   key_size=12,     # 20
	                   multi_probe_level=1) #2
	image1 = img1.img_source.read();
	image2 = img2.img_source.read();
	gimage1 = cv.cvtColor(image1, cv.COLOR_BGR2GRAY);
	gimage2 = cv.cvtColor(image2, cv.COLOR_BGR2GRAY);
	surfer = cv.SURF(400);
	key_points1 = surfer.detect(gimage1);
	surfer_descriptor = cv.DescriptorExtractor_create("SURF");
	descripters1 = surfer_descriptor.compute(image1,key_points1);
	key_points2 = surfer.detect(image2); 
	descripters2 = surfer_descriptor.compute(image2,key_points2);
	flann_matcher = cv.FlannBasedMatcher(dict(algorithm = FLANN_INDEX_KDTREE,
                    trees = 4),{});
	matches = flann_matcher.match(descripters1[1],descripters2[1]);
	good_matches = [];
	min_dist = matches[1].distance;
	for match in matches:
		if match.distance < min_dist:
			min_dist = match.distance
	for match in matches:
		if match.distance <= 2*min_dist:
			good_matches.append(match)
	i = 0;
	average_dist = 0;
	width, heigth,depth = image1.shape
	dists = [];	
	for match in good_matches:
		i +=1;
		x1, y1 = key_points1[match.queryIdx].pt
		x2, y1 = key_points2[match.trainIdx].pt
		average_dist += (width - x1) + x2;
		dists.append((width - x1) + x2)
		
	average_dist /= i;
	#logging.debug("Distances: %r" % dists)
	offset = 1;
	return average_dist 
	
flann_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=4)

def match_flann(desc1, desc2, r_threshold=0.6):
    flann = cv.flann_Index(desc2, flann_params)
    idx2, dist = flann.knnSearch(desc1, 2, params={})
    mask = dist[:,0] / dist[:,1] < r_threshold
    idx1 = np.arange(len(desc1))
    pairs = np.int32( zip(idx1, idx2[:,0]) )
    return pairs[mask]
