import cv2 as cv
import Tkinter as tk
import tkSimpleDialog
import numpy as np
from PIL import Image
from PIL import ImageTk
import logging

from display.tactical import TacticalDisplay

DEFAULT_VIEWPORT_SIZE = (400, 300)
VIEWPORT_PADDING = 10

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
        self.frame.grid(columnspan=2, rowspan=2, sticky=(tk.N, tk.S))

        # Tactical frame
        self.tactical_frame = tk.Frame(self.frame, 
                width=TacticalDisplay.WIDTH, 
                height=TacticalDisplay.HEIGHT)
        self.tactical_frame.grid(column=1, row=0, rowspan=2)

        size = DEFAULT_VIEWPORT_SIZE

        pos = [0, 0]
        for img_proc in image_processors:
            self.addView(img_proc, pos, size)
            pos[1] = pos[1] + 1

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
        # Update GUI elements
        self.root.update()
        self.root.after(0, update_func)

    def addView(self, img_proc, pos={'x':0, 'y':0}, size=(0, 0)):
        name = img_proc.img_source.name
        self.viewports[name] = Viewport(img_proc, self.frame, pos, size)
        self.viewports[name].view.bind('<Button-1>', lambda e:
                                 self.viewports[name].addCalibrationPoint([e.x, e.y]))


class Viewport(object):
    def __init__(self, img_proc, parent, pos={'x':0, 'y':0}, size=[0, 0]):
        self.img_proc = img_proc
        self.view = tk.Label(parent, cursor='tcross')
        self.pos = pos
        self.size = size
        self.cal_points = []
        if 'x' in self.pos:
            self.view.place(**pos)
        else:
            self.view.grid(column=self.pos[0], row=self.pos[1])
    
    def addCalibrationPoint(self, point):
        from processors.data import distance

        logging.debug(point)
        point = [int(float(point[0] - 2) / float(self.size[0]) *
                     self.img_proc.img_source.width), 
                 int(float(point[1] - 2) / float(self.size[1]) *
                     self.img_proc.img_source.height)]

        if len(self.cal_points) < 6:
            self.cal_points.append(point)
        else:
            closest_point_index = None
            dist = float('inf')
            for index, cal_point in enumerate(self.cal_points):
                calc_dist = distance(cal_point, point)
                if (calc_dist < dist):
                    closest_point_index = index
                    dist = calc_dist
            self.cal_points[closest_point_index] = point

        if len(self.cal_points) == 6:
            logging.debug("Saving new calibration points %s" % self.cal_points)
            self.img_proc.scm.calibrate(self.cal_points)

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
        from processors.detection import DETECT_MIN, DETECT_MAX
        hue_range = [0, 180]
        sat_range = [0, 255]
        val_range = [0, 255]

        self.color_ranges = [DETECT_MIN, DETECT_MAX]
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
