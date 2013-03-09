#!/usr/bin/env python
import gui
from image_sources import Camera
from image_sources import ImageFile
from processors import ImageProcessor

import sys
from ConfigParser import SafeConfigParser
import logging

class App(object):

	def __init__(self, config):
		self.config = config

		# Setup processors
		self.image_processors = []
		if (config.get('main', 'image_source') == 'CAMERA'):
			cam_offset = config.getint('camera', 'camera_offset')
			cam_count = config.getint('camera', 'camera_count')
			cam_size = (config.getint('camera', 'camera_size_x'),
						config.getint('camera', 'camera_size_y'))
			for cap_index in range(cam_offset, cam_offset + cam_count):
				camera = Camera('Cam' + str(cap_index), cap_index, cam_size)
				self.image_processors.append(ImageProcessor(camera))
		else:
			img_files = config.get('image_file', 'image_files').split(',')
			for img_file in img_files:
				img = ImageFile(img_file)
				self.image_processors.append(ImageProcessor(img))

		# Setup GUI
		window_title = config.get('gui', 'window_title')
		if config.get('gui', 'gui_type') == "TKINTER":
			self.ui = display.gui.Tkinter(window_title, self.image_processors)
		else:
			#TODO Fully implement HighGUI
			logging.warning('HighGUI implementation is incomplete.')
			self.ui = gui.HighGUI(window_title, image_processors)

		# Key bindings
		#TODO Clean up syntax, implement dynamic frame types
		self.ui.addKeyEvent("p", lambda: map(lambda ip: ip.saveFrame(), self.image_processors))
		#for i in range(len(ImageProcessor.frame_types)):
			#ui.addKeyEvent(str(i), lambda: map(((lambda iv: lambda ip: ip.setFrameType(iv))(i)), image_processors))
		self.ui.addKeyEvent("0", lambda: map(lambda ip: ip.setFrameType(0), self.image_processors))
		self.ui.addKeyEvent("1", lambda: map(lambda ip: ip.setFrameType(1), self.image_processors))
		self.ui.addKeyEvent("2", lambda: map(lambda ip: ip.setFrameType(2), self.image_processors))

	def run(self):
		self.ui.start(self.main)

	def main(self):
		# Get next frame from camera
		for img_proc in self.image_processors:
			frame = img_proc.process()
			self.ui.updateView(img_proc.img_source.name, frame)

		self.ui.update(self.main)


if __name__ == "__main__":
	# Load configuration
	config = SafeConfigParser()
	config_file = 'defaults.ini'
	try:
		config.readfp(open(config_file))
	except:
		logging.error('Configuration file "%s" not found' % config_file)
		sys.exit(1)
	config.read(config.get('DEFAULT', 'user_config_file'))
	
	# Configure logger
	logging.basicConfig(
			level=getattr(logging, config.get('logger', 'log_level')),
			format=config.get('logger', 'log_format', raw=True))

	# Run application
	App(config).run()
