import cv2 as cv
import numpy as np
import logging

from data import DataProcessor
from display.gui.tkinter import InputDialog

AVG_WEIGHT = 0.01
BW_THRESHOLD = 20

DETECT_MIN = np.array([0, 154, 109], np.uint8)
DETECT_MAX = np.array([37, 255, 255], np.uint8)

class ImageProcessor(object):
	# Frames to conditionally display
	frame_types = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')

	def __init__(self, img_source, frame_type=0, data_proc=None):
		self.img_source = img_source
		self.last_frame = None
		self.__avg_frame = None
		self.frame_type = self.frame_types[frame_type]
		self.coverage_size = [17, 10]
		self.coverage_offset = [0, 0]
		# Temporary polynomial variables
		self.A = 0.4386 #0.1916
		self.B = 1.6007 #1.7223
		self.C = -0.0615 #-0.0754

		if data_proc is None:
			self.data_proc = DataProcessor()
		else:
			self.data_proc = data_proc
	
	def process(self):
		self.last_frame = self.img_source.read()
		if self.avg_frame is None:
			self.avg_frame = self.last_frame
		#self.last_frame, self.avg_frame = processImage(self.last_frame, self.avg_frame, self.frame_type)
		self.last_frame, self.avg_frame, img_data = findObjects(self.last_frame, self.avg_frame, self.frame_type)

		self.data_proc.process(img_data, self)

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
	
	def setCoverageOffset(self, root):
		inputs = {'Coverage Offset X:': self.coverage_offset[0], 'Coverage Offset Y:': self.coverage_offset[1]}
		data = InputDialog(root, ('%s Coverage Offset' % self.img_source.name), inputs).result
		if data:
			self.coverage_offset = [float(data['Coverage Offset X:']), float(data['Coverage Offset Y:'])]
			logging.info("Coverage offset: %s" % self.coverage_offset)

	def setCoverageSize(self, root):
		inputs = {'Coverage Width:': self.coverage_size[0], 'Coverage Range:': self.coverage_size[1]}
		data = InputDialog(root, ('%s Coverage Size' % self.img_source.name), inputs).result
		if data:
			self.coverage_size = [float(data['Coverage Width:']), float(data['Coverage Range:'])]
			logging.info("Coverage size: %s" % self.coverage_size)
	
	def setPolynomials(self, root):
		inputs = {'A': self.A, 'B': self.B, 'C': self.C}
		data = InputDialog(root, ('%s Polynomial Vars' % self.img_source.name), inputs).result
		if data:
			[self.A, self.B, self.C] = [float(data['A']), float(data['B']), float(data['C'])]
			logging.info("Polynomials: %d + %dx + %dx^2" % (self.A, self.B, self.C))

def findObjects(frame, avg_frame, frame_type=ImageProcessor.frame_types[0]):
	blur_frame = cv.GaussianBlur(frame, (19, 19), 0)
	hsv_frame = cv.cvtColor(blur_frame, cv.COLOR_BGR2HSV)
	thresh_frame = cv.inRange(hsv_frame, DETECT_MIN, DETECT_MAX)

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
