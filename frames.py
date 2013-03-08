import cv2 as cv
from Tkinter import *
#from Tkinter import ttk

#def will go up here with the inputs and how they map to a spot on the screen

root = Tk()
root.title("WENDE Tactical Display v1")

mainframe = Frame(root, padding="3 3 12 12")
mainframe.grid(column=1, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

Label(mainframe, text="cam1").grid(column=1, row=3, sticky=W)
Label(mainframe, text="cam2").grid(column=3, row=3, sticky=E)
Label(mainframe, text="GUI Tracker").grid(column=2, row=1, sticky=N)

c = Canvas(root)
c.create_line(10, 10, 20, 20, tags=('firstline', 'drawing'))
c.create_rectangle(30, 30, 40, 40, tags=('drawing'))
c.addtag('rectangle', 'withtag', 2)
c.addtag('polygon', 'withtag', 'rectangle')
c.gettags(2)
c.dtag(2, 'polygon')
c.gettags(2)
c.find_withtag('drawing')
              
