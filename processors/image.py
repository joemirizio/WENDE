import cv2 as cv
import numpy as np

from data import DataProcessor

AVG_WEIGHT = 0.01
BW_THRESHOLD = 20


class ImageProcessor(object):
	# Frames to conditionally display
	frame_types = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')

	def __init__(self, img_source, frame_type=0):
		self.img_source = img_source
		self.last_frame = None
		self.__avg_frame = None
		self.frame_type = self.frame_types[frame_type]

		self.data_proc = DataProcessor()
	
	def process(self):
		self.last_frame = self.img_source.read()
		if self.avg_frame is None:
			self.avg_frame = self.last_frame
		#self.last_frame, self.avg_frame = processImage(self.last_frame, self.avg_frame, self.frame_type)
		self.last_frame, self.avg_frame, img_data = findObjects(self.last_frame, self.avg_frame, self.frame_type)

		self.data_proc.process(img_data)

		return self.last_frame

	@property
	def avg_frame(self):
		return self.__avg_frame
	@avg_frame.setter
	def avg_frame(self, frame):
		if self.__avg_frame is None:
			self.__avg_frame = np.float32(frame)
		else:
			self.__avg_frame = frame

	def saveFrame(self, filename=""):
		self.img_source.save(filename, self.last_frame)

	def setFrameType(self, frame_type):
		if isinstance(frame_type, basestring):
			if frame_type in self.frame_types:
				self.frame_type = frame_type
			else:
				raise Exception("Invalid frame type '%s'" % frame_type)
		else:
			self.frame_type = self.frame_types[frame_type]


BLUE_MIN = np.array([90, 50, 50], np.uint8)
BLUE_MAX = np.array([120, 255, 255], np.uint8)
def findObjects(frame, avg_frame, frame_type=ImageProcessor.frame_types[0]):
	blur_frame = cv.GaussianBlur(frame, (19, 19), 0)
	hsv_frame = cv.cvtColor(blur_frame, cv.COLOR_BGR2HSV)
	thresh_frame = cv.inRange(hsv_frame, BLUE_MIN, BLUE_MAX)

	# Calculate contours
	bw_copy = thresh_frame.copy()
	contours, hier = cv.findContours(bw_copy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

	# Draw countours and bounding boxes
	main_frame = frame.copy()
	for contour in contours:
		rect = cv.boundingRect(contour)
		top  = rect[0:2]
		bot  = (rect[0] + rect[2], rect[1] + rect[3])
		cv.rectangle(main_frame, top, bot, (255, 0, 0), 1)
	cv.drawContours(main_frame, contours, -1, (0, 255, 0), -1)

	frames = dict(zip(ImageProcessor.frame_types, (main_frame, frame, thresh_frame)))
	out_frame = frames[frame_type]


	return (out_frame, avg_frame, contours)
	
def processImage(frame, avg_frame, frame_type=ImageProcessor.frame_types[0]):
	# Blur and average with previous frames
	src_frame = cv.GaussianBlur(frame, (19, 19), 0)
	cv.accumulateWeighted(src_frame, avg_frame, AVG_WEIGHT)
	conv_frame = cv.convertScaleAbs(avg_frame)

	# Subtract current and average frames
	diff_frame = cv.absdiff(src_frame, conv_frame)

	# Convert to grayscale then to black/white
	gray_frame = cv.cvtColor(diff_frame, cv.COLOR_RGB2GRAY)
	_, bw_frame = cv.threshold(gray_frame, BW_THRESHOLD, 255, cv.THRESH_BINARY)

	# Calculate contours
	bw_copy = bw_frame.copy()
	contours, hier = cv.findContours(bw_copy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

	# Draw countours and bounding boxes
	main_frame = frame.copy()
	for contour in contours:
		rect = cv.boundingRect(contour)
		top  = rect[0:2]
		bot  = (rect[0] + rect[2], rect[1] + rect[3])
		cv.rectangle(main_frame, top, bot, (255, 0, 0), 1)
	cv.drawContours(main_frame, contours, -1, (0, 255, 0), -1)

	# Select desired frame to display
	frames = dict(zip(ImageProcessor.frame_types, (main_frame, frame, src_frame, conv_frame, gray_frame, bw_frame)))
	out_frame = frames[frame_type]

	return (out_frame, avg_frame)
