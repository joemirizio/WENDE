import logging
import Tkinter as tk

class TacticalDisplay(object):
        
        def __init__(self, display, data_proc):
                self.display = display
                self.data_proc = data_proc
                h = 250
                w = 500
                self.canvas = tk.Canvas(self.display, bg="white", height=h, width=w)
                self.canvas.pack()

        def displayTarget(self, target):
                logging.info("displayTarget: %s" % target)
                #TODO Add display logic here - dots that follow the target - tracer     

        def update(self):
                # Initialize - background things
                #coord = [10, 50, 240, 210]
                #self.canvas.create_arc(coord, start=0, extent=150, fill="red")
                #coordinates of arcs, Top Left x and y, Bottom Right x and y
                predictionTx = 0
                predictionTy = 0
                predictionBx = 500
                predictionBy = 500

                alertTx = 50
                alertTy = 50
                alertBx = 450
                alertBy = 450

                safeTx = 100
                safeTy = 100
                safeBx = 400
                safeBy = 400
                
                coordPre = predictionTx, predictionTy, predictionBx, predictionBy
                coordAlert = alertTx, alertTy, alertBx, alertBy
                coordSafe = safeTx, safeTy, safeBx, safeBy
                Pre = self.canvas.create_arc(coordPre, start = 30, extent = 120, fill="yellow")
                Alert = self.canvas.create_arc(coordAlert, start=30, extent=120, fill="red")
                Safe = self.canvas.create_arc(coordSafe, start=30, extent=120, fill="green")
                
                for target in self.data_proc.targets:
                        self.displayTarget(target)
