#!/usr/bin/env python
import cv2 as cv
import numpy as np
from Tkinter import *
from PIL import Image
from PIL import ImageTk

import sys

WINDOW_TITLE = "W.E.N.D.E. - Test"
CAMERA_COUNT = 2
#CAMERA_SIZE = (1024, 768)
CAMERA_SIZE = (800, 600)
AVG_WEIGHT = 0.01
BW_THRESHOLD = 20

def init():
	for i, camera in enumerate(cameras):
		camera.avg_frame = camera.read()
	main()

def main():
	# Get next frame from camera
	for i, camera in enumerate(cameras):
		frame = camera.read()
		frame, camera.avg_frame = processImage(frame, camera.avg_frame)
		gui.updateCamera(camera.name, frame)

	gui.update(main);

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


class Camera(object):
	def __init__(self, name, capture, size):
		self.camera = capture
		self.name = name
		self.width = size[0]
		self.height = size[1]
		self.__avg_frame = None
		capture.set(3, self.width)
		capture.set(4, self.height)

	def read(self):
		_, frame = self.camera.read()
		frame = cv.flip(frame, 1)
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


class Tkinter_gui:
	def __init__(self, name, cameras={}):
		self.root = Tk()
		self.root.title(name)
		self.labels = {}

		pos = {'x':0, 'y':0}
		for camera in cameras:
			self.addCamera(camera, pos)
			pos['x'] += camera.width

		# Fullscreen
		w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
		self.root.geometry("%dx%d+0+0" % (w, h))
		self.root.wm_state('zoomed')
		#self.root.overrideredirect(True)
		self.root.attributes('-topmost', True)


		self.root.focus_set()
		self.root.bind("<Escape>", lambda e: e.widget.quit())

	def start(self, init_func):
		self.root.after(0, init_func)
		self.root.mainloop()
	
	def update(self, update_func):
		self.root.update()
		self.root.after(0, update_func)

	def addCamera(self, camera, pos={'x':0, 'y':0}):
		label = Label(self.root)
		label.place(**pos)
		self.labels[camera.name] = label

	def updateCamera(self, name, frame):
		img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
		pil_img = Image.fromarray(img)
		photo = ImageTk.PhotoImage(pil_img)
		self.labels[name]['image'] = photo
		self.labels[name].photo = photo


class HighGui_gui:
	def __init__(self, name, cameras={}):
		self.name = name
		for camera in cameras:
			self.addCamera(camera)

	def start(self, init_func):
		init_func()
	
	def update(self, update_func):
		update_func()

	def addCamera(self, camera):
		cv.namedWindow(self.name + camera.name, cv.CV_WINDOW_AUTOSIZE)

	def updateCamera(self, name, frame):
		cv.imshow(self.name + name, frame)


if __name__ == "__main__":
	# Define frames to conditionally display
	frame_types = ('main', 'orig', 'blur', 'avg', 'gray', 'bw')
	selected_frame = frame_types[0]

	# Setup cameras
	cameras = []
	for cap_index in range(CAMERA_COUNT):
		capture = cv.VideoCapture(cap_index)
		camera = Camera('Cam' + str(cap_index), capture, CAMERA_SIZE)
		cameras.append(camera)

	gui = Tkinter_gui(WINDOW_TITLE, cameras)
	#gui = HighGui_gui(WINDOW_TITLE, cameras)

	gui.start(init)
