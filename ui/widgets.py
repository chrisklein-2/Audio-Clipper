""" widgets.py - small reusable widgets for the UI. """
from PySide6.QtWidgets import QFrame, QLineEdit, QPushButton


# Thin vertical separator line
def sep():

    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Plain)
    return line


# General purpose QPushButton builder.
# Only `text` is required. Everything else is optional and skipped if left at
# its default, so a button only needs the lines that make it different.
#
#   text         - label shown on the button
#   on_click     - function connected to clicked
#   tooltip      - hover text
#   object_name  - name used by the stylesheet (e.g. "record", "tiny")
#   min_width    - minimum width in pixels (0 = leave alone)
#   fixed_width  - exact width in pixels (0 = leave alone)
#   checkable    - True makes it a toggle button
#   checked      - starting state of a toggle button (needs checkable=True)
#   enabled      - False starts the button greyed out
#   on_toggled   - function connected to toggled (toggle buttons only)
#   size_policy  - (horizontal, vertical) tuple of QSizePolicy values
def make_button(text, on_click=None, *, tooltip="", object_name="",
                min_width=0, fixed_width=0, checkable=False, checked=False,
                enabled=True, on_toggled=None, size_policy=None):

    button = QPushButton(text)

    if object_name:
        button.setObjectName(object_name)
    if min_width:
        button.setMinimumWidth(min_width)
    if fixed_width:
        button.setFixedWidth(fixed_width)
    if size_policy:
        button.setSizePolicy(*size_policy)
    if tooltip:
        button.setToolTip(tooltip)
    if checkable:
        button.setCheckable(True)
        button.setChecked(checked)

    button.setEnabled(enabled)

    # Connect signals last so the setup above doesn't trigger them
    if on_click:
        button.clicked.connect(on_click)
    if on_toggled:
        button.toggled.connect(on_toggled)
    return button


# General purpose QLineEdit builder. Same idea as make_button.
#
#   text         - starting text
#   placeholder  - grey hint text shown when the box is empty
#   tooltip      - hover text
#   min_width    - minimum width in pixels (0 = leave alone)
#   fixed_width  - exact width in pixels (0 = leave alone)
#   on_return    - function connected to returnPressed (Enter key)
def make_line_edit(text="", *, placeholder="", tooltip="",
                   min_width=0, fixed_width=0, on_return=None):

    box = QLineEdit(text)

    if placeholder:
        box.setPlaceholderText(placeholder)
    if tooltip:
        box.setToolTip(tooltip)
    if min_width:
        box.setMinimumWidth(min_width)
    if fixed_width:
        box.setFixedWidth(fixed_width)
    if on_return:
        box.returnPressed.connect(on_return)
    return box


# QPushButton wired to a QAction.
# Text, tooltip (with shortcut), and enabled state all follow the action.
#   primary   - True gives it the "primary" stylesheet look
#   min_width - minimum width in pixels (0 = leave alone)
def action_button(action, primary=False, min_width=0):

    button = QPushButton(action.text())
    tip = action.text()

    if not action.shortcut().isEmpty():
        tip += f"   [{action.shortcut().toString()}]"

    button.setToolTip(tip)
    button.setEnabled(action.isEnabled())
    button.clicked.connect(action.trigger)

    # Keep the button's enabled state in sync with the action
    action.changed.connect(
        lambda button=button, action=action: button.setEnabled(action.isEnabled()))

    if primary:
        button.setObjectName("primary")
    if min_width:
        button.setMinimumWidth(min_width)
    return button


# Add several widgets to a layout in one call.
#   a widget        -> added normally
#   None            -> a separator line is added
#   (widget, n)     -> added with stretch factor n
def add_widgets(layout, *items):

    for item in items:
        if item is None:
            layout.addWidget(sep())
        elif isinstance(item, tuple):
            widget, stretch = item
            layout.addWidget(widget, stretch)
        else:
            layout.addWidget(item)


# Add a row of action buttons to a layout.
# `actions` is a list of QActions, with None meaning "separator here".
def add_action_buttons(layout, actions):

    for action in actions:
        layout.addWidget(sep() if action is None else action_button(action))
