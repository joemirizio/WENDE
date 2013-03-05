#!/usr/bin/env python
import gui
from image_sources import Camera
from image_sources import ImageFile
from processors import ImageProcessor

import logging
logging.basicConfig(level=logging.DEBUG)

WINDOW_TITLE = "W.E.N.D.E."
CAMERA_COUNT = 2
#CAMERA_SIZE = (1024, 768)
CAMERA_SIZE = (800, 600)

def init():
	main()

	# Key bindings
	#TODO: Clean up syntax, implement dynamic frame types
	ui.addKeyEvent("p", lambda: map(lambda ip: ip.img_source.save(), image_processors))
	#for i in range(len(ImageProcessor.frame_types)):
		#ui.addKeyEvent(str(i), lambda: map(((lambda iv: lambda ip: ip.setFrameType(iv))(i)), image_processors))
	ui.addKeyEvent("0", lambda: map(lambda ip: ip.setFrameType(0), image_processors))
	ui.addKeyEvent("1", lambda: map(lambda ip: ip.setFrameType(1), image_processors))

def main():
	# Get next frame from camera
	for img_proc in image_processors:
		frame = img_proc.process()
		ui.updateView(img_proc.img_source.name, frame)

	ui.update(main)


if __name__ == "__main__":
	# Setup processors
	image_processors = []
	for cap_index in range(CAMERA_COUNT):
		camera = Camera('Cam' + str(cap_index), cap_index, CAMERA_SIZE)
		image_processors.append(ImageProcessor(camera))
		#img = ImageFile('../camview.jpg')
		#image_processors.append(ImageProcessor(img))

	ui = gui.Tkinter(WINDOW_TITLE, image_processors)
	#ui = gui.HighGUI(WINDOW_TITLE, image_processors)

	ui.start(init)
