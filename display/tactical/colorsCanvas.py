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

top = Tkinter.Tk()
C = Tkinter.Canvas(top, bg="blue", height=250, width=300)

coord = 10, 50, 240, 210
C.create_arc(coord, start=0, extent=150, fill="red")

C.pack()
top.mainloop()

#id = create_rectangle((10, 10, 30, 30), fill="red")
#tag_bind(id, "<Button-1>", lambda x: setColor("red"))

#root = Tk()
#root.columnconfigure(0, weight=1)
#root.rowconfigure(0, weight=1)

#canvas = Canvas(root)
#canvas.grid(column=0, row=0)
#canvas.bind("<Button-1>", xy)
#canvas.bind("<B1-Motion>", addline)

canvas.create_line(10, 10, 200, 50, fill='red', width=2)

root.mainloop()
