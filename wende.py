#!/usr/bin/env python

import sys
from ConfigParser import SafeConfigParser
import logging
import os

import display.gui
from processors.image import image
from processors.image import ImageProcessor
from processors.data import DataProcessor
#from processors.data import correlation
from display.tactical import TacticalDisplay
from display.gui.tkinter_gui import ColorDialog


class App(object):

    def __init__(self, config):
        self.config = config

        # Setup processors
        self.data_processor = DataProcessor(self)
        self.image_processors = image.createImageProcessors(self)
#        self.corr = correlation.CorrelationModule(self)

        # Setup GUI
        window_title = config.get('gui', 'window_title')
        if config.get('gui', 'gui_type') == "TKINTER":
            self.ui = display.gui.Tkinter_gui(window_title, self)
        else:
            #TODO Fully implement HighGUI
            logging.warning('HighGUI implementation is incomplete.')
            self.ui = gui.HighGUI(window_title, image_processors)

        # Tactical display
        self.tactical = TacticalDisplay(self.ui.top_frame.tactical_frame, self.data_processor)
        
        # Key bindings
        #TODO Clean up syntax, implement dynamic frame types
        self.ui.addKeyEvent("p", lambda: map(lambda ip: ip.saveFrame(processed=False), self.image_processors))
        self.ui.addKeyEvent("r", lambda: map(lambda ip: ip.isi.startRecord(), self.image_processors))
        self.ui.addKeyEvent("e", lambda: map(lambda ip: ip.isi.stopRecord(), self.image_processors))
        #for i in range(len(ImageProcessor.frame_types)):
            #ui.addKeyEvent(str(i), lambda: map(((lambda iv: lambda ip: ip.setFrameType(iv))(i)), image_processors))
        self.ui.addKeyEvent("0", lambda: map(lambda ip: ip.setFrameType(0), self.image_processors))
        self.ui.addKeyEvent("1", lambda: map(lambda ip: ip.setFrameType(1), self.image_processors))
        self.ui.addKeyEvent("2", lambda: map(lambda ip: ip.setFrameType(2), self.image_processors))
        #self.ui.addKeyEvent("d", lambda: map(lambda ip: ip.scm.calibrate(), self.image_processors))
        self.ui.addKeyEvent("c", lambda: ColorDialog(self.ui.root))
        self.ui.addKeyEvent("q", lambda: self.tactical.clearTargetData())
        self.ui.addKeyEvent("k", lambda: map(lambda ip: ip.scm.saveCalibrationData(), self.image_processors))
        self.ui.addKeyEvent("l", lambda: map(lambda ip: ip.scm.loadCalibrationData(), self.image_processors))
        self.ui.addKeyEvent("d", lambda: self.tactical.toggleRunningDogTest())

    def run(self):
        self.ui.start(self.main)

    def main(self):

        # Image Processors
        for image_processor in self.image_processors:
            image_processor.process()
    
        # Data Processor
        self.data_processor.process()

        #TODO Remove after testing
        for target in self.data_processor.targets:
            target.clearProcessedThisCycle()

        self.tactical.update()
        self.ui.update(self.main)

if __name__ == "__main__":
    # Load configuration
    config = SafeConfigParser()
    config_file = os.path.join('config', 'defaults.ini')
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
    if config.getboolean('logger', 'use_log_file'):
        logger = logging.getLogger()
        hdlr = logging.FileHandler(config.get('logger', 'log_file'))
        logger.addHandler(hdlr)

    # Run application
    App(config).run()

