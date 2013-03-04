#!/usr/bin/env python
import gui
from image_sources import Camera
from image_sources import ImageFile
from processors import ImageProcessor

WINDOW_TITLE = "W.E.N.D.E."
CAMERA_COUNT = 1
#CAMERA_SIZE = (1024, 768)
CAMERA_SIZE = (800, 600)

def init():
	main()

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
