import cv2 as cv
import numpy as np

AVG_WEIGHT = 0.01
BW_THRESHOLD = 20

# Define frames to conditionally display
frame_types = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')
selected_frame = frame_types[0]

class ImageProcessor(object):
	def __init__(self, img_source):
		self.img_source = img_source
		self.__avg_frame = None
	
	def process(self):
		frame = self.img_source.read()
		if self.avg_frame is None:
			self.avg_frame = frame
		frame, self.avg_frame = processImage(frame, self.avg_frame)
		return frame

	@property
	def avg_frame(self):
		return self.__avg_frame
	@avg_frame.setter
	def avg_frame(self, frame):
		if self.__avg_frame is None:
			self.__avg_frame = np.float32(frame)
		else:
			self.__avg_frame = frame

	
def processImage(frame, avg_frame):
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
	frames = dict(zip(frame_types, (main_frame, frame, src_frame, conv_frame, gray_frame, bw_frame)))
	out_frame = frames[selected_frame]

	return (out_frame, avg_frame)
