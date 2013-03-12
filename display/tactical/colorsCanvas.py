#color frames

#from Tkinter import *
import Tkinter
import tkMessageBox

lastx, lasty = 0, 0

def xy(event):
    global lastx, lasty
    lastx, lasty = event.x, event.y

def addLine(event):
    global lastx, lasty
    create_line((lastx, lasty, event.x, event.y))
    lastx, lasty = event.x, event.y

def setColor(newcolor):
    global color
    color = newcolor

#def callback(event):
#    canvas = event.widget
#    x = canvas.canvasx(event.x)
#    y = canvas.canvasy(event.y)
#    print canvas.find_closest(x, y)
    
top = Tkinter.Tk()
x=500
y=250

#this doesnt work but should change the coordinate system
#def callback(event):
#    h = Tkinter.Canvas.canvasy(event.x)
#    w = Tkinter.Canvas.canvasyx(event.y)
    
C = Tkinter.Canvas(top, bg="white", height=y, width=x)

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
#coord = topLeftx, topLefty, bottomRx, bottomRy
#currently set so the point of wedge at 250
coordPre = predictionTx, predictionTy, predictionBx, predictionBy
coordAlert = alertTx, alertTy, alertBx, alertBy
coordSafe = safeTx, safeTy, safeBx, safeBy
Pre = C.create_arc(coordPre, start = 30, extent = 120, fill="#33B5E5")
Alert = C.create_arc(coordAlert, start=30, extent=120, fill="#FF4444")
Safe = C.create_arc(coordSafe, start=30, extent=120, fill="#99CC00")

#tracking circle
C.create_oval(225, 125, 230, 130, fill="black")
C.create_line(225, 127, 250, 127, fill="black")

C.pack()
top.mainloop()
