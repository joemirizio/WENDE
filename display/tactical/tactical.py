import Tkinter as tk
import math
import logging
from datetime import datetime

# TODO Cleanup this reference..
PERSIST_TIME = 30 # Seconds # This seems reasonable.. right?
MAXLEN_DEQUE = PERSIST_TIME * 50 # Just.. just save pretty much all of them for now

class TacticalDisplay(object):
    
    PADDING = 50
    WIDTH = 800
    HEIGHT = WIDTH / 2
    SIZE = (WIDTH, HEIGHT)
    MAX_RANGE = 12
    MAX_WIDTH = MAX_RANGE * math.cos(math.radians(30)) * 2
    LABEL_OFFSET = [0, 35]

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
        from processors.data import distance
        
        # Remove expired targets
        remove_list = self.findExpiredTargets()
        self.removeTarget(remove_list)
        
        # Display targets
        for target in self.data_proc.targets:
            self.displayTarget(target)

            # Display alerts
            # TODO Cleanup logic
            if distance((0, 0), target.pos) < 5:
                target.left_safe = False
            elif distance((0, 0), target.pos) < 10:
                target.left_alert = False
            
            if distance((0, 0), target.pos) >= 10 and target.left_alert == False:
                self.data_proc.tca.ui.displayAlert("Target has left the Alert zone")
                target.left_alert = True
                target.left_safe = True
            elif distance((0, 0), target.pos) >= 5 and target.left_safe == False:
                self.data_proc.tca.ui.displayAlert("Target entered the Alert zone")
                target.left_alert = False
                target.left_safe = True

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
        target_pos_points = self.getBoundingBox(0.25, pos=target_pos)
        label_pos = [
                target_pos[0] + TacticalDisplay.PADDING - TacticalDisplay.LABEL_OFFSET[0],
                target_pos[1] + TacticalDisplay.PADDING - TacticalDisplay.LABEL_OFFSET[1]]
        label_text = "(%.2f, %.2f)" % (target.pos[0], target.pos[1])

        # Display target and track
        if target not in self.tgtTracks:
            # Create target icon
            tgtTrack = TargetTrack(target)
            tgtTrack.icon = self.canvas.create_oval(target_pos_points, fill="#AA66CC", outline="#9933CC", width=4)
            # Create label
            tgtTrack.label = tk.Label(self.canvas, text=label_text, bg='white', anchor='s')
            # Add label_toggle
            self.canvas.tag_bind(tgtTrack.icon, "<Button-1>", lambda e: tgtTrack.toggleLabelVisibility())
            self.tgtTracks[target] = tgtTrack
        else:
            # Draw track lines
            tgtTrack = self.tgtTracks[target] 
            if len(tgtTrack.target.filtered_positions) > 2:
                # Remap track positions
                track_pts = tgtTrack.target.filtered_positions
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
                else:
                    self.canvas.coords(tgtTrack.track, *track_points)

        # Draw target icon
        self.canvas.coords(tgtTrack.icon, *target_pos_points)
        self.canvas.tag_raise(tgtTrack.icon)
        
        # Update target label
        tgtTrack.label.config(text=label_text)
        
        # Toggle visibility
        if tgtTrack.display_label:
            tgtTrack.label.place(x=label_pos[0], y=label_pos[1])
        else:
            tgtTrack.label.place_forget()
            
        tgtTrack.label_pos = label_pos

        # Draw prediction line and label
        if tgtTrack.target.predLineIntersect:
            
            # Determine current line position
            current_pos = tgtTrack.target.pos
            prediction_pos = [self.remapPosition(current_pos),
                              self.remapPosition(tgtTrack.target.predLineIntersect)]
            prediction_pos = flattenArray(prediction_pos)
            prediction_pos = ([coord + TacticalDisplay.PADDING for coord in
                                prediction_pos])
            
            # Create or redraw line
            if not tgtTrack.prediction:
                tgtTrack.prediction = self.canvas.create_line(*prediction_pos, fill="#090600",
                                            width=2, capstyle="round")
            else:
                self.canvas.coords(tgtTrack.prediction, *prediction_pos)
                
            # Determine prediction label position
            prediction_point = self.remapPosition(tgtTrack.target.predLineIntersect)
            prediction_point_box = self.getBoundingBox(0.15, pos=prediction_point)
            label_pos = [
                    prediction_point[0] + TacticalDisplay.PADDING - TacticalDisplay.LABEL_OFFSET[0],
                    prediction_point[1] + TacticalDisplay.PADDING - TacticalDisplay.LABEL_OFFSET[1]]
            label_text = "(%.2f, %.2f)" % (tgtTrack.target.predLineIntersect[0], 
                                           tgtTrack.target.predLineIntersect[1])
    
            # Create icon and label if this is first prediction
            if not tgtTrack.label_prediction:
                # Create prediction icon
                tgtTrack.icon_prediction = self.canvas.create_oval(prediction_point_box, fill="#090600", width=2)
                # Create label
                tgtTrack.label_prediction = tk.Label(self.canvas, text=label_text, bg='white', anchor='s')
                
            # Draw prediction icon
            self.canvas.coords(tgtTrack.icon_prediction, *prediction_point_box)
            self.canvas.tag_raise(tgtTrack.icon_prediction)

            # Update prediction label
            tgtTrack.label_prediction.config(text=label_text)
            tgtTrack.label_prediction.place(x=label_pos[0], y=label_pos[1])

    def remapPosition(self, pos):
        return [float(pos[0]) / float(TacticalDisplay.MAX_RANGE * 2) * TacticalDisplay.WIDTH + (TacticalDisplay.WIDTH / 2), 
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
        
    def findExpiredTargets(self):
        """ Finds targets which have exceeded the maximum time between updates 
        
        Returns a list of expired targets
        
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
        """ Removes targets from display 
        
        Arguments --
            remove_list - List containing targets marked for removal
            
        """
        
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
        self.label_pos = None
        self.display_label = True
        self.icon_prediction = None
        self.label_prediction = None
    
    def removeDisplayObjects(self, canvas):
        canvas.delete(self.icon)
        canvas.delete(self.track)
        canvas.delete(self.prediction)
        canvas.delete(self.icon_prediction)
        self.label.destroy()
        if self.label_prediction:
            self.label_prediction.destroy()

    def toggleLabelVisibility(self):
        self.display_label = not self.display_label

def flattenArray(arr):
    # Flatten points in array
    return [item for sublist in arr for item in sublist]
