"""
Contains the individual graphical components that are assembled together with
Tkinter to create the graphical user interface. These components are divided
into two primary areas: the top frame and bottom frame. The top frame contains
the main menu, the tactical display, and the zone size selector. Viewports,
calibration status indicators, and the alert message box appear in the lower
frame.  

Classes:
    Tkinter_gui
    Viewport
    Alert
    InputDialog
    ColorDialog
    TopFrame
    BotFrame
    MenuCal
    MenuMain
    InfoBar
    MultiRadio
"""

import cv2 as cv
import Tkinter as tk
import tkFont
import tkSimpleDialog
import numpy as np
from PIL import Image
from PIL import ImageTk
from Tkinter import Scrollbar
import logging
import math
import datetime

from display.tactical import TacticalDisplay

DEFAULT_VIEWPORT_SIZE = (400, 300)
VIEWPORT_PADDING = 10
ALERT_DURATION = 5

LOGGER_WIDTH = 51
PAD_MENU = 91

COLOR_LIGHT = '#4E4D4A'
COLOR_DARK = '#353432'


class Tkinter_gui(object):
    """Generates and displays the Graphical User Interface for the Tactical Computer Application. 

    Attributes:
        root: A root window object.
        viewports: A list of Viewport objects.
        key_events: A list of key press events.
        tca: Tactical Computer Application.
        frame: A Tkinter frame.
        top_frame: A TopFrame object.
        bot_frame: A BotFrame object. 

    Methods:
        callbackShell()
        addKeyEvent()
        keyPress()
        start()
        update()
        addView()
        displayAlert()
        logAlert()
    """
    def __init__(self, name, tca):
        self.root = tk.Tk()
        self.root.title(name)
        self.viewports = {}
        self.key_events = {}
        self.tca = tca

        # Fullscreen
        #w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        #self.root.geometry("%dx%d+0+0" % (w, h))
        # self.root.wm_state('zoomed')
        # self.root.overrideredirect(True)
        #self.root.attributes('-topmost', True)
        self.root.resizable(0, 0)
        self.root.focus_set()

        # Main frame
        self.frame = tk.Frame(self.root, bg=COLOR_LIGHT)
        self.frame.grid(rowspan=3, sticky=(tk.N, tk.S))

        # Top Frame
        self.top_frame = TopFrame(self.frame, self, self.tca.image_processors,
                                  bg=COLOR_DARK, padx=0, pady=0)

        # Bottom Frame
        self.bot_frame = BotFrame(self.frame, self, self.tca.image_processors,
                                  bg=COLOR_LIGHT, padx=0, pady=0)
        self.bot_frame.addViewports()

        # Grid Frames
        self.top_frame.grid(row=0, column=0)
#         self.mid_frame.grid(row=1, column=0)
        self.bot_frame.grid(row=2, column=0, pady=(0, 5))

        self.root.bind("<Escape>", lambda e: e.widget.quit())

    def callbackShell(self):
        pass

    def addKeyEvent(self, key, event):
        """Handles simultaneous key press events.        

        Args:
            key: A key-press event.
            event: An event. 
        """
        if key in self.key_events:
            raise Exception("Callback already registered to %s" % key)
        self.key_events[key] = event

    def keyPress(self, event):
        """Handles a key press event.        

        Args:
            event: An event. 
        """
        for key, callback in self.key_events.iteritems():
            if event.char == key:
                callback()

    def start(self, init_func):
        """Initiates running the main window loop. A provided initial function will be run first.        

        Args:
            init_func: A string specifying the initial function to run. 
        """
        self.root.bind("<Key>", self.keyPress)
        self.root.after(0, init_func)
        self.root.mainloop()

    def update(self, update_func):
        """Updates viewports, alerts, labels, and other specified GUI elements.       

        Args:
            update_func: A string specifying the update function to run.
        """
        # Update viewports
        for viewport in self.viewports.itervalues():
            viewport.update()
        # Update alert
        self.alert.update()
        # Update viewport labels
        self.bot_frame.update()
        # Update GUI elements
        self.root.update()
        self.root.after(0, update_func)

    def addView(self, img_proc, parent, pos={'x': 0, 'y': 0}, size=(0, 0)):
        """Adds a new viewport to the GUI. 
        
        Args:
            img_proc: An ImageProcessor object.
            parent: A parent widget.
            pos: A 2-D position coordinate.
            size: A x,y list of the viewport window resolution. 
        """
        name = img_proc.isi.name
        self.viewports[name] = Viewport(img_proc, parent, pos, size)

        # Bind correct calibration method
        if img_proc.config.get('calibration', 'cal_manual_method') == "POINT":
            self.viewports[name].view.bind('<Button-1>', lambda e:
                                           self.viewports[name].addCalibrationPoint(
                                               [e.x,
                                                e.y]))
        elif img_proc.config.get('calibration', 'cal_manual_method') == "COLOR":
            self.viewports[name].view.bind('<Button-1>', lambda e:
                                           self.viewports[name].addCalibrationColor(
                                               [e.x,
                                                e.y]))

    def displayAlert(self, label_text):
        """Displays an alert message.       

        Args:
            label_text: A string containing the alert message text. 
        """
        self.alert.displayAlert(label_text)

    def logAlert(self, label_text):
        """Adds an alert message to the alert log.       

        Args:
            label_text: A string containing the alert message text. 
        """
        self.alert.logAlert(label_text)


class Viewport(object):
    """The viewport object displays frames from the image sources in the GUI. 

    Attributes:
        img_proc: An ImageProcessor object.
        view: A viewport Label object.
        pos: A 2-D position coordinate.
        size: A x,y list of the viewport window resolution.
        cal_points: A list of 2-D calibration coordinates.
        cal_thresholds: A list of DetectionThreshold objects. 

    Methods:
        addCalibrationPoint()
        addCalibrationColor()
        update()
    """
    def __init__(self, img_proc, parent, pos={'x': 0, 'y': 0}, size=[0, 0]):
        self.img_proc = img_proc
        self.view = tk.Label(parent, cursor='tcross', borderwidth=0)
        self.pos = pos
        self.size = size
        self.cal_points = []
        self.cal_thresholds = []
        if 'x' in self.pos:
            self.view.place(**pos)
        else:
            self.view.grid(column=self.pos[0], row=self.pos[1])

    def addCalibrationPoint(self, point):
        """Adds the provided point to the list of calibration points and initiates calibration if all points received. 
        
        Args:
            point: x and y coordinate of clicked point
        """
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
        """Collects the color from clicked points and uses it to find calibration points
        
        Args:
            point: x and y coordinate of clicked point
        """

        from processors.image.detection import buildDetectionThresholds
        from processors.image.calibration import SourceCalibrationModule

        # Get last frame and convert point using viewpoint size
        frame = cv.cvtColor(self.img_proc.last_frame, cv.COLOR_BGR2HSV)
        point = [int(float(point[0] - 2) / float(self.size[0]) *
                     self.img_proc.isi.width),
                 int(float(point[1] - 2) / float(self.size[1]) *
                     self.img_proc.isi.height)]

        # Format as array and switch to format [height, width] for indexing
        point = np.array([point[1], point[0]])

        # Create box around clicked point
        if (point - 1. < [0, 0]).any():
            surrounding_box = frame[
                point[0]:point[0] + 3, point[1]:point[1] + 3]
        elif (point + 1 > [self.img_proc.isi.height, self.img_proc.isi.width]).any():
            surrounding_box = frame[
                point[0] - 2:point[0] + 1, point[1] - 2:point[1] + 1]
        else:
            surrounding_box = frame[
                point[0] - 1:point[0] + 2, point[1] - 1:point[1] + 2]

        # Average HSV values in box and build thresholds
        color_average = np.mean(surrounding_box, axis=(0, 1)).astype(np.uint8)
        cal_thresholds = buildDetectionThresholds(color_average)

        logging.debug('Clicked Color: %s' % color_average)
        logging.debug('detection min: %s' % cal_thresholds.min)
        logging.debug('detection max: %s' % cal_thresholds.max)

        # Set center calibration colors and show detections
        if self.cal_thresholds == []:
            self.cal_thresholds.append(cal_thresholds)
            self.img_proc.scm.setCalibrationThresholds(
                'center', self.cal_thresholds)
            self.img_proc.scm.setDisplayColors(True, False)
        # Set side calibration colors and delete thresholds
        else:
            self.cal_thresholds.append(cal_thresholds)
            self.img_proc.scm.setCalibrationThresholds(
                'all', self.cal_thresholds)
            self.img_proc.scm.setDisplayColors(True, True)
            self.cal_thresholds = []

    def update(self):
        """Updates viewports to display most recent frame and calibration circles.       

        Args:
            None
        """
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
    """A system alert object.

    Attributes:
        root: A root window object.
        expire_time: Date and time when an alert will expire.
        label_text: A string variable containing the alert message text and timestamp.
        alert_log: A Tkinter text object containing recent alert messages.
        scrollbar: A Scrollbar object.

    Methods:
        createItems()
        update()
        displayAlert()
        logAlert()
        clear()
    """
    def __init__(self, root):

        self.root = root
        self.expire_time = None

        self.label_text = None
        self.alert_log = None
        self.scrollbar = None

        self.createItems()

    def createItems(self):
        """Creates an alert label and an alert logging window.       

        Args:
            None
        """
        self.label_text = tk.StringVar()
        font = tkFont.Font(family="Verdana", size=16, weight='bold')

        # Alert label
        alert_label = tk.Label(self.root, font=font, fg='white',
                               textvariable=self.label_text, bg=COLOR_LIGHT,
                               pady=5)
        alert_label.grid(
            row=0, column=0, columnspan=3, sticky=(tk.N + tk.W + tk.E))

        # Set scrollbar
        self.scrollbar = Scrollbar(self.root)
        self.scrollbar.grid(row=1, column=1, sticky=tk.NS)

        # Alert logging window
        self.alert_log = tk.Text(
            self.root, state='disabled', width=LOGGER_WIDTH + 2, height=12, bg='white',
            wrap='word', relief=tk.FLAT, yscrollcommand=self.scrollbar.set)
        self.alert_log.grid(row=1, column=0, sticky=(tk.N + tk.S))

        self.scrollbar.config(command=self.alert_log.yview)

    def update(self):
        """Initiates an alert erase if the alert time has expired.       

        Args:
            alert_text: A string containing the alert message text. 
        """
        if self.expire_time and datetime.datetime.now() > self.expire_time:
            self.clear()

    def displayAlert(self, alert_text):
        """Displays an alert message.       

        Args:
            alert_text: A string containing the alert message text. 
        """
        import re
        ts = datetime.datetime.now().strftime("%H:%M:%S ")
        str_temp = ts + alert_text
        self.label_text.set(re.sub('\t', '', str_temp))
        self.expire_time = (datetime.datetime.now() +
                            datetime.timedelta(seconds=ALERT_DURATION))

    def logAlert(self, alert_text):
        """Adds an alert to the alert log list.       

        Args:
            alert_text: A string containing the alert message text.
        """
        self.label_text.set('')
        self.expire_time = None
        ts = datetime.datetime.now().strftime("%H:%M:%S ")
        self.label_text.set(ts + alert_text)

        numlines = self.alert_log.index('end - 1 line').split('.')[0]
        self.alert_log['state'] = 'normal'

        if numlines == 10:
            self.alert_log.delete(1.0, 2.0)
        if self.alert_log.index('end-1c') != '1.0':
            self.alert_log.insert('end', '\n')

        self.alert_log.insert('end', self.label_text.get())
        self.alert_log.yview(tk.END)
        self.alert_log['state'] = 'disabled'

    def clear(self):
        """Clears an alert message.       

        Args:
            None
        """
        self.label_text.set('')
        self.expire_time = None


class InputDialog(tkSimpleDialog.Dialog):

    def __init__(self, parent, title=None, inputs={'Value': 0}):
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

        self.color_ranges = [
            detection.ObjectDetectionModule.TARGET_THRESHOLDS.min,
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


class TopFrame(tk.Frame):
    """The upper GUI window frame that contains main menu, tactical, and area size selector frames.

    Attributes:
        parent: A parent widget.
        ui: A Tkinter_gui object.
        image_processors: A list of ImageProcessor objects.
        bg: A string naming the background color.
        menu_main: A MenuMain frame.
        tactical_frame: A Tkinter frame in which the tactical data will be displayed.
        menu_cal: A MenuCal frame. 

    Methods:
        createItems()
        callbackSetZone()
    """
    def __init__(self, parent, ui, image_processors, **options):
        tk.Frame.__init__(self, parent, options)
        self.parent = parent
        self.ui = ui
        self.image_processors = image_processors
        self.bg = self.cget('bg')

        self.menu_main = None
        self.tactical_frame = None
        self.menu_cal = None

        self.createItems()

    def createItems(self):
        """Creates the main menu, tactical, and area size selector frames.       

        Args:
            None
        """
        # Main menu frame
        self.menu_main = MenuMain(
            self, self.ui, self.image_processors, bg=self.bg, highlightthickness=0)
        self.menu_main.pack(side=tk.LEFT, padx=PAD_MENU, fill=tk.X, expand=1)

        # Tactical frame
        self.tactical_frame = tk.Frame(self, bg=self.bg)
        self.tactical_frame.pack(side=tk.LEFT, padx=0, fill=tk.BOTH, expand=1)

        # Calibration menu frame
        self.menu_cal = MenuCal(
            self, self.ui, self.image_processors, bg=self.bg, highlightthickness=0)
        self.menu_cal.pack(side=tk.LEFT, padx=PAD_MENU, fill=tk.X, expand=1)


class BotFrame(tk.Frame):
    """The bottom GUI window frame that contains alert info label, calibration status, and image source viewports.

    Attributes:
        parent: A parent widget.
        ui: A Tkinter_gui object.
        image_processors: A list of ImageProcessor objects.
        bg_light: The background color value.
        bg: A string naming the background color.
        string_caltext: A string list indicating the status of calibration for each image processor.
        label_caltext: A list of calibration status label objects.
        label_calcolor: A list of label objects for the calibration status color indicator.
        label_alert: A label object for the Alert Messages header.

    Methods:
        createItems()
        callbackSetZone()
    """
    def __init__(self, parent, ui, image_processors, **options):

        tk.Frame.__init__(self, parent, options)
        self.parent = parent
        self.ui = ui
        self.image_processors = image_processors
        self.bg_light = COLOR_LIGHT
        self.bg = self.cget('bg')
        self.string_caltext = []
        self.label_caltext = []
        self.label_calcolor = []
        self.label_alert = None

        self.createCalLabels()
        self.createAlerts()

    def addViewports(self):
        """Add image source viewports to the GUI.       

        Args:
            None
        """
        # Raw Feeds
        pos = [2, 1]
        for img_proc in self.image_processors:
            self.ui.addView(img_proc, self, pos, DEFAULT_VIEWPORT_SIZE)
            pos[0] = pos[0] - 2

    def createCalLabels(self):
        """Create frame for alert info label, calibration status, and viewports.       

        Args:
            None
        """ 
                # Frame for viewport info labels
        pos = 2
        for feed in xrange(len(self.image_processors)):
            # Create subframe
            frame = tk.Frame(self, bg=self.bg_light)
            # Create text and labels
            string_caltext = tk.StringVar()
            self.string_caltext.append(string_caltext)

            label = tk.Label(
                frame, textvariable=string_caltext, font=(
                    "Verdana", 10, "bold"),
                borderwidth=0, width=LOGGER_WIDTH / 2, bg=self.bg_light, padx=0, pady=0)
            label.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=0, pady=0)
            self.label_caltext.append(label)

            label = tk.Label(
                frame, borderwidth=0, width=LOGGER_WIDTH / 2, padx=0, pady=0)
            label.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=0, pady=0)
            self.label_calcolor.append(label)

            # Grid and change position
            frame.grid(row=0, column=pos, sticky=(tk.W + tk.E + tk.N + tk.S))
            pos = pos - 2

        # Frame for alert info label
        frame = tk.Frame(self, padx=0, pady=0, bg=self.bg)
        self.label_alert = tk.Label(frame, text="Alert Messages",
                                    font=("Verdana", 16, "bold"),
                                    bg=self.bg_light, fg="#353432")
        self.label_alert.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        frame.grid(row=0, column=1, sticky=(tk.W + tk.E))

    def createAlerts(self):
        """Create alerts and alert frame.       

        Args:
            None
        """
        self.alert_frame = tk.Frame(self, bg=COLOR_LIGHT)
        self.ui.alert = Alert(self.alert_frame)
        self.alert_frame.grid(row=1, column=1, sticky=(tk.S))

    def update(self):
        """Updates the GUI bottom frame with the current calibration status.       

        Args:
            None
        """
        for index, img_proc in enumerate(self.image_processors):
            if img_proc.cal_data.is_valid:
                self.string_caltext[index].set("Calibrated")
                self.label_calcolor[index].config(bg='green')
            else:
                self.string_caltext[index].set("Uncalibrated")
                self.label_calcolor[index].config(bg='red')


class MenuCal(tk.Frame):
    """A demonstration area size selector frame.

    Attributes:
        parent: A parent widget.
        ui: A Tkinter_gui object.
        image_processors: A list of ImageProcessor objects.
        zone: A radio selector frame object.

    Methods:
        createItems()
        callbackSetZone()
    """
    def __init__(self, parent, ui, image_processors, **options):

        tk.Frame.__init__(self, parent, options)
        self.parent = parent
        self.ui = ui
        self.image_processors = image_processors
        self.method = None
        self.zone = None

        # Build Menu Interface
        self.createItems()

    def createItems(self):
        """Creates the demonstration area size radio selector.        

        Args:
            None
        """
# Calibrate Button
#         tk.Button(self, text="Calibrate\nSystem", font=("Verdana", 12, "bold"),
#                   pady=10, padx=2, bg='green', relief=tk.FLAT,
#                   command=self.callbackCalibrate).pack(side=tk.TOP, pady=10)
#
# Simple separator (Horizontal)
#         separator = tk.Frame(self, width=2, height=2, bd=1, relief=tk.FLAT)
#         separator.pack(side=tk.TOP, pady=10, padx=5, fill=tk.X)
#
# Calibration Method
#         tk.Label(self, text="Calibration\nMethod", font=("Verdana", 10, "bold"), bg=COLOR_LIGHT).pack(side=tk.TOP, fill=tk.X)
#         self.method = MultiRadio(self,
#                                     text=("Point", "Color"), value=("POINT", "COLOR"),
#                                     callback=self.callbackCalibrate,
#                                     side=tk.TOP, fill=tk.X).pack(fill=tk.X, side=tk.TOP)
#
# Simple separator (Horizontal)
#         separator = tk.Frame(self, width=2, height=2, bd=1, relief=tk.FLAT)
#         separator.pack(side=tk.TOP, pady=10, padx=5, fill=tk.X)

        # Zone Type
        tk.Label(self, text="Zone Type", font=("Verdana", 10, "bold"),
                 bg=COLOR_LIGHT).pack(side=tk.TOP, fill=tk.X)
        self.zone = MultiRadio(self,
                               text=("Normal", "Small"), value=("NORMAL", "SMALL"),
                               callback=self.callbackSetZone,
                               side=tk.TOP, fill=tk.X)
        self.zone.variable.set("NORMAL")
        self.zone.pack(fill=tk.X, side=tk.TOP)

#     def callbackCalibrate(self):
#         if self.method.variable == "POINT":
#             pass
#         else:
#             pass

    def callbackSetZone(self):
        """Callback for the demo area size selector. Initiates calibration and tactical display background scaling.        

        Args:
            None
        """
        from processors.image.calibration import SourceCalibrationModule

        # Set zone distances
        for img_proc in self.image_processors:
            img_proc.scm.setCalibrationDistances(self.zone.variable.get())

        # Redraw tactical background
        # TODO Remove static reference
        self.ui.tca.tactical.drawBackground(
            SourceCalibrationModule.ZONE_DISTANCES)

        logging.debug('setting zone distances %s' % self.zone.variable.get())


class MenuMain(tk.Frame):
    """A main menu frame containing the system power and clear targets buttons.

    Attributes:
        parent: A parent widget.
        ui: A Tkinter_gui object.
        text_power: A string variable indicating the system power state.
        button_power: The power button object.
        button_clear: The Clear Targets button object.

    Methods:
        createItems()
        callbackPower()
        callbackClear()
    """
    def __init__(self, parent, ui, image_processors, **options):

        tk.Frame.__init__(self, parent, options)
        self.parent = parent
        self.ui = ui
        self.text_power = tk.StringVar()
        self.button_power = None
        self.button_clear = None

        self.text_power.set("Stop\nSystem")

        # Build Menu Interface
        self.createItems()

    def createItems(self):
        """Creates the system start/stop and clear targets buttons.       

        Args:
            None
        """
        # Power Button
        self.button_power = tk.Button(self, textvariable=self.text_power,
                                      font=("Verdana", 14, "bold"),
                                      pady=10, padx=2, bg='red', relief=tk.FLAT,
                                      command=self.callbackPower)
        self.button_power.pack(side=tk.TOP, pady=10)

        # Simple separator (Horizontal)
        separator = tk.Frame(self, width=2, height=2, bd=1, relief=tk.FLAT)
        separator.pack(side=tk.TOP, pady=10, padx=5, fill=tk.X)

        # Clear Button
        self.button_clear = tk.Button(
            self, text="Clear\nTargets", font=("Verdana", 12, "bold"),
            pady=10, padx=2, bg='yellow', relief=tk.FLAT,
            command=self.callbackClear)
        self.button_clear.pack(side=tk.TOP, pady=10)

    def callbackPower(self):
        """Callback for the TCA system start/stop button.       

        Args:
            None
        """
        # Start system
        # ......
        self.ui.tca.data_processor.toggleActive()

        # Change button text and color

        if self.ui.tca.data_processor.is_active:
            self.text_power.set("Stop\nSystem")
            self.button_power.config(bg='red')
        else:
            self.text_power.set("Start\nSystem")
            self.button_power.config(bg='green')

    def callbackClear(self):
        """Erases all target data from the tactical display.       

        Args:
            None
        """
        self.ui.tca.tactical.clearTargetData()


class InfoBar(tk.Frame):
    """An infobar frame.

    Attributes:
        parent: A parent widget.
        image_processors: A list of ImageProcessor objects.
        string_caltext: A string list indicating the status of calibration for each image processor.
        label_caltext: A list of calibration status label objects.
        label_calcolor: A list of label objects for the calibration status color indicator.
        label_alert: A label object for the Alert Messages header.

    Methods:
        createItems()
        update()
    """
    def __init__(self, parent, image_processors, **options):

        tk.Frame.__init__(self, parent, options)
        self.parent = parent
        self.image_processors = image_processors
        self.string_caltext = []
        self.label_caltext = []
        self.label_calcolor = []
        self.label_alert = None

        # Build Menu Interface
        self.createItems()

    def createItems(self):
        """Creates the GUI infobar.       

        Args:
            None
        """
        # Frame for viewport info labels
        pos = 0
        for feed in xrange(len(self.image_processors)):
            # Create subframe
            frame = tk.Frame(self, relief=tk.FLAT, padx=0, pady=0)
            # Create text and labels
            string_caltext = tk.StringVar()
            self.string_caltext.append(string_caltext)

            label = tk.Label(
                frame, textvariable=string_caltext, font=(
                    "Verdana", 10, "bold"),
                borderwidth=0, width=LOGGER_WIDTH / 2, bg=self.cget('bg'), padx=0, pady=0)
            label.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=0, pady=0)
            self.label_caltext.append(label)

            label = tk.Label(
                frame, borderwidth=0, width=LOGGER_WIDTH / 2, padx=0, pady=0)
            label.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, padx=0, pady=0)
            self.label_calcolor.append(label)

            # Grid and change position
            frame.grid(row=0, column=pos, sticky=(tk.W + tk.E))
            pos = pos + 2

        # Frame for alert info label
        frame = tk.Frame(self, relief=tk.FLAT, padx=0, pady=0)
        self.label_alert = tk.Label(
            frame, text="Alert Messages", font=("Verdana", 10, "bold"),
            width=LOGGER_WIDTH, bg=self.cget('bg'))
        self.label_alert.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        frame.grid(row=0, column=1, sticky=(tk.W + tk.E))

    def update(self):
        """Updates the GUI infobar with the current calibration status.       

        Args:
            None
        """
        pos = 0
        for img_proc in self.image_processors:
            if img_proc.cal_data.is_valid:
                self.string_caltext[pos].set("Calibrated")
                self.label_calcolor[pos].config(bg='green')
            else:
                self.string_caltext[pos].set("Uncalibrated")
                self.label_calcolor[pos].config(bg='red')
            pos = pos + 1


class MultiRadio(tk.Frame):
    """A radio button frame for the demonstration area size selector.

    Attributes:
        createRadio: A Tkinter variable.
        text: A string label for the radio button.
        value: String value assigned to each radio button selection.
        callback: The callbackSetZone object.
        side: A variable that specifies the orientation of radio selections.
        fill: Integer that specifies the pixel separation between radio selections.

    Methods:
        createRadio()
    """
    def __init__(self, parent, text, value, callback, side=tk.TOP, fill=tk.NONE):

        tk.Frame.__init__(self, parent, borderwidth=0, relief=tk.FLAT)

        self.createRadio = tk.StringVar()
        self.text = text
        self.value = value
        self.callback = callback
        self.side = side
        self.fill = fill

        self.createRadio()

    def createRadio(self):
        """Creates a radio button.       

        Args:
            None
        """
        # Zone size select buttons
        for txt, val, in zip(self.text, self.value):
            tk.Radiobutton(self, text=txt, font=("Verdana", 10),
                           variable=self.variable, value=val, indicatoron=0,
                           command=self.callback, padx=0, pady=0).pack(side=self.side, fill=self.fill)
