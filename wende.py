#!/usr/bin/env python

import display.gui
from image_sources import Camera
from image_sources import ImageFile
from image_sources import VideoFile
from processors import ImageProcessor
from processors import DataProcessor
from display.tactical import TacticalDisplay
from display.gui.tkinter_gui import ColorDialog

import sys
from ConfigParser import SafeConfigParser
import logging

class App(object):

    def __init__(self, config):
        self.config = config

        # Setup processors
        self.data_processor = DataProcessor()
        self.image_processors = []
        if (config.get('main', 'image_source') == 'CAMERA'):
            cam_offset = config.getint('camera', 'camera_offset')
            cam_count = config.getint('camera', 'camera_count')
            cam_size = (config.getint('camera', 'camera_size_x'),
                        config.getint('camera', 'camera_size_y'))
            for cap_index in range(cam_offset, cam_offset + cam_count):
                camera = Camera('Cam' + str(cap_index), cap_index, cam_size)
                img_proc = ImageProcessor(self, camera, config, data_proc=self.data_processor)
                self.image_processors.append(img_proc)
        elif (config.get('main', 'image_source') == 'VIDEO_FILE'):
            video_files = config.get('video_file', 'video_files').split(',')
            for video_file_index, video_file in enumerate(video_files):
                video_size = (config.getint('video_file', 'video_size_x'),
                            config.getint('video_file', 'video_size_y'))
                video_name = 'Video' + str(video_file_index)
                video = VideoFile(video_name, video_file, video_size)
                img_proc = ImageProcessor(self, video, config, data_proc=self.data_processor)
                self.image_processors.append(img_proc)
        else:
            img_files = config.get('image_file', 'image_files').split(',')
            for img_file in img_files:
                img = ImageFile(img_file)
                img_proc = ImageProcessor(self, img, config, data_proc=self.data_processor)
                self.image_processors.append(img_proc)

        # Setup GUI
        window_title = config.get('gui', 'window_title')
        if config.get('gui', 'gui_type') == "TKINTER":
            self.ui = display.gui.Tkinter_gui(window_title, self.image_processors)
        else:
            #TODO Fully implement HighGUI
            logging.warning('HighGUI implementation is incomplete.')
            self.ui = gui.HighGUI(window_title, image_processors)

        # Tactical display
        self.tactical = TacticalDisplay(self.ui.tactical_frame, self.data_processor)
        
        # Key bindings
        #TODO Clean up syntax, implement dynamic frame types
        self.ui.addKeyEvent("p", lambda: map(lambda ip: ip.saveFrame(), self.image_processors))
        self.ui.addKeyEvent("r", lambda: map(lambda ip: ip.img_source.startRecord(), self.image_processors))
        self.ui.addKeyEvent("e", lambda: map(lambda ip: ip.img_source.stopRecord(), self.image_processors))
        #for i in range(len(ImageProcessor.frame_types)):
            #ui.addKeyEvent(str(i), lambda: map(((lambda iv: lambda ip: ip.setFrameType(iv))(i)), image_processors))
        self.ui.addKeyEvent("0", lambda: map(lambda ip: ip.setFrameType(0), self.image_processors))
        self.ui.addKeyEvent("1", lambda: map(lambda ip: ip.setFrameType(1), self.image_processors))
        self.ui.addKeyEvent("2", lambda: map(lambda ip: ip.setFrameType(2), self.image_processors))
        self.ui.addKeyEvent("d", lambda: map(lambda ip: ip.scm.calibrate(), self.image_processors))
        self.ui.addKeyEvent("c", lambda: ColorDialog(self.ui.root))

    def run(self):
        self.ui.start(self.main)

    def main(self):
        # Get next frame from camera
        for img_proc in self.image_processors:
            frame = img_proc.process()

        self.tactical.update()
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
