import cv2 as cv
import Tkinter as tk
import tkFont
import tkSimpleDialog
import numpy as np
from PIL import Image
from PIL import ImageTk
import logging
import math
import datetime

from display.tactical import TacticalDisplay

DEFAULT_VIEWPORT_SIZE = (400, 300)
VIEWPORT_PADDING = 10
ALERT_DURATION = 5

class Tkinter_gui(object):
    def __init__(self, name, image_processors={}):
        self.root = tk.Tk()
        self.root.title(name)
        self.viewports = {}
        self.key_events = {}

        # Fullscreen
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+0+0" % (w, h))
        #self.root.wm_state('zoomed')
        #self.root.overrideredirect(True)
        #self.root.attributes('-topmost', True)
        self.root.focus_set()

        # Main frame
        self.frame = tk.Frame(self.root)
        self.frame.grid(columnspan=3, rowspan=3, sticky=(tk.N, tk.S))

        # Tactical frame
        self.tactical_frame = tk.Frame(self.frame, 
                width=TacticalDisplay.WIDTH, 
                height=TacticalDisplay.HEIGHT)
        self.tactical_frame.grid(column=0, row=0, columnspan=2, rowspan=2)
        
        # Calibration Frame
        self.menu = MenuBar(self.frame).grid(column=0, row=4, columnspan=2)

        size = DEFAULT_VIEWPORT_SIZE

        # Alerts
        self.alert = Alert(self.root)

        # Raw Feed
        pos = [0, 3]
        for img_proc in image_processors:
            self.addView(img_proc, pos, size)
            pos[0] = pos[0] + 1

        self.root.bind("<Escape>", lambda e: e.widget.quit())


    def addKeyEvent(self, key, event):
        if key in self.key_events:
            raise Exception("Callback already registered to %s" % key)
        self.key_events[key] = event

    def keyPress(self, event):
        for key, callback in self.key_events.iteritems():
            if event.char == key:
                callback()

    def start(self, init_func):
        self.root.bind("<Key>", self.keyPress)
        self.root.after(0, init_func)
        self.root.mainloop()
    
    def update(self, update_func):
        # Update viewports
        for viewport in self.viewports.itervalues():
            viewport.update()
        # Update alert
        self.alert.update()
        # Update GUI elements
        self.root.update()
        self.root.after(0, update_func)

    def addView(self, img_proc, pos={'x':0, 'y':0}, size=(0, 0)):
        name = img_proc.isi.name
        self.viewports[name] = Viewport(img_proc, self.frame, pos, size)
        
        # Bind correct calibration method
        if img_proc.config.get('calibration','cal_manual_method') == "POINT":
            self.viewports[name].view.bind('<Button-1>', lambda e:
                                           self.viewports[name].addCalibrationPoint([e.x, 
                                                                                     e.y]))
        elif img_proc.config.get('calibration','cal_manual_method') == "COLOR":
            self.viewports[name].view.bind('<Button-1>', lambda e:
                                           self.viewports[name].addCalibrationColor([e.x, 
                                                                                     e.y]))
        
    def displayAlert(self, label_text):
        self.alert.displayAlert(label_text)
        

class Viewport(object):
    def __init__(self, img_proc, parent, pos={'x':0, 'y':0}, size=[0, 0]):
        self.img_proc = img_proc
        self.view = tk.Label(parent, cursor='tcross')
        self.pos = pos
        self.size = size
        self.cal_points = []
        self.cal_thresholds = []
        if 'x' in self.pos:
            self.view.place(**pos)
        else:
            self.view.grid(column=self.pos[0], row=self.pos[1])
    
    def addCalibrationPoint(self, point):
        from processors.data import distance

        logging.debug(point)
        point = [int(float(point[0] - 2) / float(self.size[0]) *
                     self.img_proc.isi.width), 
                 int(float(point[1] - 2) / float(self.size[1]) *
                     self.img_proc.isi.height)]

        if len(self.cal_points) < 6:
            self.cal_points.append(point)
        else:
            # Reassign closest calibration point to new point
            closest_point_index = None
            dist = float('inf')
            for index, cal_point in enumerate(self.cal_points):
                calc_dist = distance(cal_point, point)
                if (calc_dist < dist):
                    closest_point_index = index
                    dist = calc_dist
            self.cal_points[closest_point_index] = point

        # Save new calibration points and recalibrate image processor
        if len(self.cal_points) == 6:
            logging.debug("Saving new calibration points %s" % self.cal_points)
            self.img_proc.scm.calibrate(self.cal_points)
            

    def addCalibrationColor(self, point):
        """ Collects the color from clicked points and uses it to find calibration points
        
        Arguments:
            point -- x and y coordinate of clicked point
            
        """
        
        from processors.image.detection import buildDetectionThresholds
        from processors.image.calibration import SourceCalibrationModule
        
        # Get last frame and convert point using viewpoint size
        frame =  cv.cvtColor(self.img_proc.last_frame, cv.COLOR_BGR2HSV)
        point = [int(float(point[0] - 2) / float(self.size[0]) *
                     self.img_proc.isi.width), 
                 int(float(point[1] - 2) / float(self.size[1]) *
                     self.img_proc.isi.height)]
        
        # Format as array and switch to format [height, width] for indexing
        point = np.array([point[1], point[0]])
        
        # Create box around clicked point
        if (point-1. < [0,0]).any():
            surrounding_box = frame[point[0]:point[0]+3, point[1]:point[1]+3]
        elif (point+1 > [self.img_proc.isi.height, self.img_proc.isi.width]).any():
            surrounding_box = frame[point[0]-2:point[0]+1, point[1]-2:point[1]+1]
        else:
            surrounding_box = frame[point[0]-1:point[0]+2, point[1]-1:point[1]+2]
            
        # Average HSV values in box and build thresholds
        color_average = np.mean(surrounding_box, axis=(0,1)).astype(np.uint8)
        cal_thresholds = buildDetectionThresholds(color_average)
        
        logging.debug('Clicked Color: %s' % color_average)
        logging.debug('detection min: %s' % cal_thresholds.min)
        logging.debug('detection max: %s' % cal_thresholds.max)
        
        # Set center calibration colors and show detections
        if self.cal_thresholds == []:
            self.cal_thresholds.append(cal_thresholds)
            self.img_proc.scm.setCalibrationThresholds('center', self.cal_thresholds)
            self.img_proc.scm.setDisplayColors(True, False)
        # Set side calibration colors and delete thresholds
        else:
            self.cal_thresholds.append(cal_thresholds)
            self.img_proc.scm.setCalibrationThresholds('all', self.cal_thresholds)
            self.img_proc.scm.setDisplayColors(True, True)
            self.cal_thresholds = []

    def update(self):
        frame = self.img_proc.last_frame
        frame = cv.resize(frame, self.size)
        # Check frame dimensions if Gray or BGR and convert to RGB
        if len(frame.shape) == 2:
            img = cv.cvtColor(frame, cv.COLOR_GRAY2RGB)
        else:
            img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        
        if self.cal_points:
            for cal_point in self.cal_points:
                cal_point = tuple(cal_point)
                cv.circle(frame, cal_point, 5, [0, 255, 0], thickness=-1)
                cv.circle(frame, cal_point, 5, [0, 0, 0], thickness=2)

        # Convert to PIL
        pil_img = Image.fromarray(img)
        photo = ImageTk.PhotoImage(pil_img)
        # Set PIL to label's image
        self.view['image'] = photo
        self.view.photo = photo
        
class Alert(object):
    def __init__(self, root):
        self.label_text = tk.StringVar()
        font = tkFont.Font(family="Arial", size=24)
        self.alert_label = tk.Label(root, font=font, textvariable=self.label_text, anchor=tk.SW)
        self.alert_label.grid()
        self.expire_time = None
        
    def update(self):
        if self.expire_time and datetime.datetime.now() > self.expire_time:
            self.clear()

    def displayAlert(self, alert_text):
        self.label_text.set(alert_text)
        self.expire_time = (datetime.datetime.now() +
            datetime.timedelta(seconds=ALERT_DURATION))

    def clear(self):
        self.label_text.set('')
        self.expire_time = None
        
class InputDialog(tkSimpleDialog.Dialog):

    def __init__(self, parent, title=None, inputs={'Value':0}):
        self.inputs = inputs
        self.data = {}
        tkSimpleDialog.Dialog.__init__(self, parent, title)

    def body(self, root):
        for i, (label, def_val) in enumerate(self.inputs.iteritems()):
            tk.Label(root, text=label).grid(row=i)
            val = tk.Entry(root)
            val.insert(0, def_val)
            val.grid(row=i, column=1)
            self.data[label] = val

        # Set focus on first input
        return self.data[self.inputs.keys()[0]]

    def apply(self):
        result = {}
        for label, val in self.data.iteritems():
            result[label] = val.get()
        self.result = result

class ColorDialog(tkSimpleDialog.Dialog):

    def body(self, root):
        from processors.image import detection
        hue_range = [0, 180]
        sat_range = [0, 255]
        val_range = [0, 255]

        self.color_ranges = [detection.ObjectDetectionModule.TARGET_THRESHOLDS.min, 
                             detection.ObjectDetectionModule.TARGET_THRESHOLDS.max]
        self.colors = []
        for i in range(2):
            hue = tk.Scale(root, from_=hue_range[0], to=hue_range[1])
            hue.set(self.color_ranges[i][0].tolist())
            hue.grid(row=0, column=i)
            sat = tk.Scale(root, from_=sat_range[0], to=sat_range[1])
            sat.set(self.color_ranges[i][1].tolist())
            sat.grid(row=1, column=i)
            val = tk.Scale(root, from_=val_range[0], to=val_range[1])
            val.set(self.color_ranges[i][2].tolist())
            val.grid(row=2, column=i)
            self.colors.append([hue, sat, val])
    
    def apply(self):
        for ref, color in zip(self.color_ranges, self.colors):
            ref[0] = color[0].get()
            ref[1] = color[1].get()
            ref[2] = color[2].get()

        logging.debug("Colors: %s" % self.color_ranges)

class MenuBar(tk.Frame):
    
    def __init__(self, parent):
        
        tk.Frame.__init__(self, parent, borderwidth='2')
        self.parent = parent
        self.zone_type = tk.StringVar()
        self.zone_type.set("NORMAL")
        self.font = tkFont.Font(family='Arial', size=12, weight=tkFont.NORMAL)
        self.font_bold = self.font.copy().config(weight=tkFont.BOLD)
        
        # Build Menu Interface
        self.createMenuItems()
        
    def createMenuItems(self):
        
        # Clear Button
        tk.Button(self, text="Clear Data", font=("Verdana", 12, "bold"), bg='red',
                  padx=10, pady=2, relief=tk.FLAT,
                  command=self.callbackClear()).pack(side=tk.LEFT, padx=10)
                  
        # Simple separator
        separator = tk.Frame(self, width=2, height=2, bg='black', bd=1, relief=tk.FLAT)
        separator.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.Y)
        
        # Calibrate Button
        tk.Button(self, text="Calibrate System", font=("Verdana", 14, "bold"),
                  padx=10, pady=2, bg='green', relief=tk.FLAT, 
                  command=self.callbackCalibrate()).pack(side=tk.LEFT, padx=10)
                  
        # Simple separator
        separator = tk.Frame(self, width=2, height=2, bg='black', bd=1, relief=tk.FLAT)
        separator.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.Y)
        
        # Zone Size Label
        tk.Label(self, text="Zone Type", font=("Verdana", 10, "bold")).pack(fill=tk.X, side=tk.TOP)
        
        # Zone size select buttons
        tk.Radiobutton(self, text="Normal", font=("Verdana", 10),
                       variable=self.zone_type, value="NORMAL", indicatoron=0,
                       command=self.callbackSetZone(), padx=5, pady=0).pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(self, text="Small", font=("Verdana", 10),
                       variable=self.zone_type, value="SMALL", indicatoron=0,
                       command=self.callbackSetZone(), padx=5, pady=0).pack(side=tk.LEFT, padx=2)
                       
    def callbackClear(self):
        pass
    
    def callbackCalibrate(self):
        pass

    def callbackSetZone(self):
        pass