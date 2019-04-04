# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 12:02:02 2018

@author: Martin
"""

import sys
if sys.version_info[0] == 2:
    from Tkinter import *
else:
    from tkinter import *
from TkinterDnD2 import *

def drop(event):
    entry_sv.set(event.data)
    
    
#TK_DND_PATH = r"C:\Tools\07_Develop\Anaconda\tcl\tkdnd2.8"


root = Tk()
#root.eval('lappend auto_path {' + TK_DND_PATH + '}')
entry_sv = StringVar()
entry_sv.set('Drop Here...')
entry = Entry(root, textvar=entry_sv, width=80)
entry.pack(fill=X, padx=10, pady=10)
entry.drop_target_register(DND_FILES)
entry.dnd_bind('<<Drop>>', drop)
root.mainloop()