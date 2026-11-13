""" widgets.py - small reusable widgets for the UI. """
from PySide6.QtWidgets import QFrame, QPushButton

# Thin vertical separator line
def sep():

    f = QFrame()
    f.setFrameShape(QFrame.VLine)
    f.setFrameShadow(QFrame.Plain)
    return f

# QPushButton wired to a QAction
def abtn(action, primary=False, min_w=0):

    b = QPushButton(action.text())
    tip = action.text()

    if not action.shortcut().isEmpty():
        tip += f"   [{action.shortcut().toString()}]"
    
    b.setToolTip(tip)
    b.setEnabled(action.isEnabled())
    b.clicked.connect(action.trigger)
    
    action.changed.connect(lambda a=action, b=b: b.setEnabled(a.isEnabled()))
    
    if primary:
        b.setObjectName("primary")
    if min_w:
        b.setMinimumWidth(min_w)
    return b