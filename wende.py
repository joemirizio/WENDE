#!/usr/bin/env python
import gui
from camera import Camera
from camera import processImage

WINDOW_TITLE = "W.E.N.D.E."
CAMERA_COUNT = 1
#CAMERA_SIZE = (1024, 768)
CAMERA_SIZE = (800, 600)

def init():
	for i, camera in enumerate(cameras):
		camera.avg_frame = camera.read()
	main()

def main():
	# Get next frame from camera
	for i, camera in enumerate(cameras):
		frame = camera.read()
		frame, camera.avg_frame = processImage(frame, camera.avg_frame)
		ui.updateCamera(camera.name, frame)

	ui.update(main);


if __name__ == "__main__":
	# Setup cameras
	cameras = []
	for cap_index in range(CAMERA_COUNT):
		camera = Camera('Cam' + str(cap_index), cap_index, CAMERA_SIZE)
		cameras.append(camera)

	ui = gui.Tkinter(WINDOW_TITLE, cameras)
	#ui = gui.HighGUI(WINDOW_TITLE, cameras)

	ui.start(init)
