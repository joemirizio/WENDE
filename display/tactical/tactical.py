import Tkinter as tk
import math
import logging
from datetime import datetime

# TODO Cleanup this reference..
PERSIST_TIME = 3 # Seconds
MAXLEN_DEQUE = PERSIST_TIME * 10 # Assuming 10 FPS

class TacticalDisplay(object):
    
    PADDING = 5
    WIDTH = 800
    HEIGHT = WIDTH / 2
    SIZE = (WIDTH, HEIGHT)
    MAX_RANGE = 12
    MAX_WIDTH = MAX_RANGE * math.cos(math.radians(30)) * 2
    LABEL_OFFSET = [0, -15]

    def __init__(self, display, data_proc):
        self.display = display
        self.data_proc = data_proc
        self.tgtTracks = {}
        self.canvas = tk.Canvas(self.display, bg="#FFFFFF",
                width=TacticalDisplay.WIDTH + TacticalDisplay.PADDING, 
                height=TacticalDisplay.HEIGHT + TacticalDisplay.PADDING)
        self.canvas.grid()

        self.drawBackground()

        # Log position
        self.canvas.bind("<Button-1>", lambda e: logging.debug("Canvas (%d, %d)" % (e.x, e.y)))
        # Clear target data
        self.canvas.bind("<Button-2>", lambda e: self.clearTargetData())

    def update(self):
        
        # Remove expired targets
        remove_list = self.findExpiredTargets()
        self.removeTarget(remove_list)
        
        # Display targets
        for target in self.data_proc.targets:
            self.displayTarget(target)

    def updateCalibration(self, message):
        if message == 1:
            status = "Starting Calibration Process"
            status_pos = [80,350]
        elif message == 2:
            status = "Calibration Complete"
            status_pos = [80,370]
        else:
            status = "Uncalibrated System"
            status_pos = [80,330]

        self.canvas.create_text(status_pos, text=status)

    def displayTarget(self, target):
        # Remap target position
        target_pos = self.remapPosition(target.pos)
        #logging.debug("Mapped pos: (%d, %d)" % (target_pos[0], target_pos[1]))
        target_pos_points = self.getBoundingBox(0.3, pos=target_pos)
        label_pos = [
                target_pos[0] + TacticalDisplay.PADDING + TacticalDisplay.LABEL_OFFSET[0],
                target_pos[1] + TacticalDisplay.PADDING + TacticalDisplay.LABEL_OFFSET[1]]
        label_text = "(%.2f, %.2f)" % (target.pos[0], target.pos[1])

        # Display target and track
        if target not in self.tgtTracks:
            # Create target icon
            tgtTrack = TargetTrack(target)
            tgtTrack.icon = self.canvas.create_oval(target_pos_points, fill="#AA66CC", outline="#9933CC", width=4)
            # Create label
            tgtTrack.label = self.canvas.create_text(*label_pos, anchor="s")
            # Add label_toggle
            self.canvas.tag_bind(tgtTrack.icon, "<Button-1>", lambda e: tgtTrack.toggleLabelVisibility())
            self.tgtTracks[target] = tgtTrack
        else:
            # Draw track lines
            tgtTrack = self.tgtTracks[target] 
            if len(tgtTrack.target.detected_positions) > 2:
                # Remap track positions
                track_pts = tgtTrack.target.detected_positions
                track_points = []
                for point in track_pts:
                    track_points.append(self.remapPosition(point))
                # Flatten and add padding
                track_points = flattenArray(track_points)
                track_points = [coord + TacticalDisplay.PADDING for coord in track_points]

                if not tgtTrack.track:
                    tgtTrack.track = self.canvas.create_line(*track_points,
                                                             fill="#FFBB33",
                                                             width=2,
                                                             capstyle="round")
                    #, smooth=1)
                else:
                    self.canvas.coords(tgtTrack.track, *track_points)

        # Draw target icon
        self.canvas.coords(tgtTrack.icon, *target_pos_points)
        self.canvas.tag_raise(tgtTrack.icon)
        # Update target label
        if not tgtTrack.display_label:
            label_text = ""
        self.canvas.coords(tgtTrack.label, *label_pos)
        self.canvas.itemconfigure(tgtTrack.label, text=label_text)

        # Prediction line
        if tgtTrack.target.predLineIntersect:
            
            current_pos = tgtTrack.target.pos
            prediction_pos = [self.remapPosition(current_pos),
                              self.remapPosition(tgtTrack.target.predLineIntersect)]
            prediction_pos = flattenArray(prediction_pos)
            prediction_pos = ([coord + TacticalDisplay.PADDING for coord in
                                prediction_pos])

            if not tgtTrack.prediction:
                tgtTrack.prediction = self.canvas.create_line(*prediction_pos, fill="#090600",
                                            width=2, capstyle="round")
            else:
                self.canvas.coords(tgtTrack.prediction, *prediction_pos)
                
            ####################################################### Create Prediction Label
            # Remap prediction position
            prediction_point = self.remapPosition(tgtTrack.target.predLineIntersect)
            prediction_point_box = self.getBoundingBox(0.1, pos=prediction_point)
            label_pos = [
                    prediction_point[0] + TacticalDisplay.PADDING + TacticalDisplay.LABEL_OFFSET[0],
                    prediction_point[1] + TacticalDisplay.PADDING + TacticalDisplay.LABEL_OFFSET[1]]
            label_text = "(%.2f, %.2f)" % (tgtTrack.target.predLineIntersect[0], 
                                           tgtTrack.target.predLineIntersect[1])
    
            # Display prediction
            if not tgtTrack.icon_prediction:
                # Create prediction icon
                tgtTrack.icon_prediction = self.canvas.create_oval(prediction_point_box, fill="#090600", width=2)
                # Create label
                tgtTrack.label_prediction = self.canvas.create_text(*label_pos, anchor="s")
                
            # Draw prediction icon
            self.canvas.coords(tgtTrack.icon_prediction, *prediction_point_box)
            self.canvas.tag_lower(tgtTrack.icon_prediction)
            # Update target label
            self.canvas.coords(tgtTrack.label_prediction, *label_pos)
            self.canvas.itemconfigure(tgtTrack.label_prediction, text=label_text)

    def remapPosition(self, pos):
        return [float(pos[0]) / float(TacticalDisplay.MAX_WIDTH) * TacticalDisplay.WIDTH + (TacticalDisplay.WIDTH / 2), 
                TacticalDisplay.HEIGHT - float(pos[1]) / float(TacticalDisplay.MAX_RANGE) * TacticalDisplay.HEIGHT]

    def getBoundingBox(self, width, height=None, pos=[float(WIDTH) / 2.0, HEIGHT]):
        if not height: height = width
        max_len = TacticalDisplay.MAX_RANGE
        pad = TacticalDisplay.PADDING

        extent_x = TacticalDisplay.WIDTH * (float(width) / float(max_len)) / 2.0
        extent_y = TacticalDisplay.HEIGHT * (float(height) / float(max_len))

        # points = [topLeftx, topLefty, bottomRx, bottomRy]
        points = [-extent_x + pos[0] + pad, -extent_y + pos[1] + pad, 
                extent_x + pos[0] + pad, extent_y + pos[1] + pad]

        return points

    def drawBackground(self):
        start_angle = 30
        sweep_angle = 120

        pred_points = self.getBoundingBox(12.0)
        alrt_points = self.getBoundingBox(10.0)
        safe_points = self.getBoundingBox(5.0)

        # Currently set so the point of wedge at 250
        pred_zone = self.canvas.create_arc(pred_points, start=start_angle, extent=sweep_angle, fill="#33B5E5", outline="#0099CC", width=4)
        alrt_zone = self.canvas.create_arc(alrt_points, start=start_angle, extent=sweep_angle, fill="#FF4444", outline="#CC0000", width=4)
        safe_zone = self.canvas.create_arc(safe_points, start=start_angle, extent=sweep_angle, fill="#99CC00", outline="#669900", width=4)

        #self.canvas.create_text([80,330], text="Uncalibrated System")
            
    def clearTargetData(self):
        for tgtTrack in self.tgtTracks.itervalues():
            tgtTrack.removeDisplayObjects(self.canvas)
        self.tgtTracks = {}
        self.data_proc.clearTargetData()
        logging.debug('removing')
        
    def findExpiredTargets(self):
        """ Finds targets which have exceeded the maximum between updates 
        
        returns a list of expired targets
        
        """
        
        remove_list = []
        
        for tgtTrack in self.tgtTracks.itervalues():
            # Check if last update is older than persistance time
            update_interval = (datetime.now() - tgtTrack.target.last_update).seconds
            
            if update_interval > PERSIST_TIME:
                # Delete from display and mark target for removal
                tgtTrack.removeDisplayObjects(self.canvas)
                remove_list.append(tgtTrack.target)
                
        return remove_list
    
    def removeTarget(self, remove_list):
        """ Removes targets from display """
        
        for target in remove_list:
            del self.tgtTracks[target]
            self.data_proc.targets.remove(target)

class TargetTrack(object):
    def __init__(self, target):
        self.target = target
        self.icon = None
        self.track = None
        self.prediction = None
        self.label = None
        self.display_label = False
        
        self.icon_prediction = None
        self.label_prediction = None
    
    def removeDisplayObjects(self, canvas):
        canvas.delete(self.icon)
        canvas.delete(self.track)
        canvas.delete(self.prediction)
        canvas.delete(self.label)
        
        canvas.delete(self.icon_prediction)
        canvas.delete(self.label_prediction)

    def toggleLabelVisibility(self):
        self.display_label = not self.display_label

def flattenArray(arr):
    # Flatten points in array
    return [item for sublist in arr for item in sublist]
