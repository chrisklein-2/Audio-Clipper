"""
dialogs.py - modal dialogs: BusyDialog, SourceDialog, JoinDialog.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton, QTextBrowser, QVBoxLayout,
    QCheckBox, QDoubleSpinBox, QGridLayout, QComboBox, QFormLayout, QLineEdit, QMessageBox
)

from audio_backends import default_device_index, list_capture_devices
from config import LOAD_FILTER
from .help_text import HELP_HTML
from processing import IMAGE_FILTER

def confirm(parent, title, text, yes_text, no_text="Cancel"):
    """Warning box with named buttons. True if the first one was clicked."""
    box = QMessageBox(QMessageBox.Warning, title, text, QMessageBox.NoButton, parent)
    yes = box.addButton(yes_text, QMessageBox.AcceptRole)
    no = box.addButton(no_text, QMessageBox.RejectRole)
    box.setDefaultButton(no)
    box.exec()
    return box.clickedButton() is yes


class BusyDialog(QDialog):
    """Progress dialog that can be a spinner or a real percentage bar."""

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setMinimumWidth(400)
        self.label = QLabel(message)
        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        lay = QVBoxLayout(self)
        lay.addWidget(self.label)
        lay.addWidget(self.bar)

    def set_progress(self, fraction):
        if self.bar.maximum() == 0:
            self.bar.setRange(0, 1000)
        self.bar.setValue(int(max(0.0, min(1.0, fraction)) * 1000))


class SourceDialog(QDialog):
    """Picks the capture source in a dialog rather than a menu."""

    def __init__(self, current_label=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select audio source")
        self.setMinimumSize(560, 340)
        self.devices = []
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(lambda _: self.accept())
        note = QLabel(
            "LOOPBACK records everything your speakers play.\n"
            "To capture Spotify alone: install VB-CABLE, set Spotify's output to\n"
            "CABLE Input in the Windows volume mixer, then pick INPUT CABLE Output here."
        )
        note.setStyleSheet("color:#9699a3;")
        refresh = QPushButton("Refresh list")
        refresh.clicked.connect(self.refresh)
        ok = QPushButton("Use this source")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(refresh)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        root = QVBoxLayout(self)
        root.addWidget(note)
        root.addWidget(self.list, 1)
        root.addLayout(buttons)
        self.refresh(current_label)

    def refresh(self, keep_label=None):
        if keep_label is None:
            current = self.list.currentItem()
            keep_label = current.data(Qt.UserRole).label if current else None
        self.devices = list_capture_devices()
        self.list.clear()
        for device in self.devices:
            item = QListWidgetItem(device.label)
            item.setData(Qt.UserRole, device)
            self.list.addItem(item)
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole).label == keep_label:
                self.list.setCurrentRow(i)
                return
        index = default_device_index(self.devices)
        if 0 <= index < self.list.count():
            self.list.setCurrentRow(index)

    def chosen(self):
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item else None


class JoinDialog(QDialog):
    """Pick several files and drag them into playback order."""

    def __init__(self, start_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join audio files")
        self.setMinimumSize(540, 330)
        self.start_dir = start_dir
        self.list = QListWidget()
        self.list.setDragDropMode(QListWidget.InternalMove)
        self.list.setToolTip("Drag to reorder. They are joined top to bottom.")
        add = QPushButton("Add files...")
        add.clicked.connect(self.add_files)
        rm = QPushButton("Remove")
        rm.clicked.connect(self.remove_selected)
        up = QPushButton("Move up")
        up.clicked.connect(lambda: self.move(-1))
        dn = QPushButton("Move down")
        dn.clicked.connect(lambda: self.move(1))
        ok = QPushButton("Join")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        side = QVBoxLayout()
        for b in (add, rm, up, dn):
            side.addWidget(b)
        side.addStretch(1)
        side.addWidget(ok)
        side.addWidget(cancel)
        body = QHBoxLayout()
        body.addWidget(self.list, 1)
        body.addLayout(side)
        root = QVBoxLayout(self)
        root.addWidget(QLabel(
            "Joined top to bottom - drag to reorder.\n"
            "Sample rate and channels convert automatically."
        ))
        root.addLayout(body, 1)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add files", self.start_dir, LOAD_FILTER
        )
        for path in paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            item.setToolTip(path)
            self.list.addItem(item)

    def remove_selected(self):
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))

    def move(self, delta):
        row = self.list.currentRow()
        target = row + delta
        if row < 0 or not (0 <= target < self.list.count()):
            return
        item = self.list.takeItem(row)
        self.list.insertItem(target, item)
        self.list.setCurrentRow(target)

    def files(self):
        return [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]


class HelpDialog(QDialog):
    """Scrollable help window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to use SpotClip")
        self.resize(680, 620)
        browser = QTextBrowser()
        browser.setHtml(HELP_HTML)
        close = QPushButton("Close")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        lay = QVBoxLayout(self)
        lay.addWidget(browser)
        lay.addWidget(close)


class PieceFadeDialog(QDialog):
    """Fade-in / fade-out for one kept piece; 'Default' follows Fade per cut."""

    def __init__(self, keep, default_s, number, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Fades for piece {number + 1}")
        self.setMinimumWidth(340)
        limit = max(0.1, min(60.0, keep.length()))
        grid = QGridLayout()
        self._rows = []
        for row, (label, value) in enumerate(
                (("Fade in", keep.fade_in), ("Fade out", keep.fade_out))):
            box = QCheckBox(f"Default ({default_s:g} s)")
            box.setChecked(value is None)
            spin = QDoubleSpinBox()
            spin.setRange(0.0, limit)
            spin.setDecimals(2)
            spin.setSingleStep(0.5)
            spin.setSuffix(" s")
            spin.setValue(min(limit, default_s if value is None else value))
            spin.setEnabled(value is not None)
            box.toggled.connect(lambda on, s=spin: s.setEnabled(not on))
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(spin, row, 1)
            grid.addWidget(box, row, 2)
            self._rows.append((box, spin))
        ok = QPushButton("Apply")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        root = QVBoxLayout(self)
        root.addWidget(QLabel(
            f"Piece length {keep.length():.1f} s. Fades are shrunk "
            f"automatically if they would overlap."))
        root.addLayout(grid)
        root.addLayout(buttons)

    def values(self):
        return tuple(None if box.isChecked() else spin.value()
                     for box, spin in self._rows)


class SettingsDialog(QDialog):
    """Every setting in one window. Applied only when OK is pressed."""

    def __init__(self, values, sample_rates, bitrates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)

        self.export_edit = QLineEdit(values["export_dir"])
        self.finals_edit = QLineEdit(values["finals_dir"])
        self.cover_edit = QLineEdit(values["cover"])
        self.cover_edit.setPlaceholderText("none")

        self.sr_box = QComboBox()
        for rate, label in sample_rates:
            self.sr_box.addItem(label, rate)
        self._select(self.sr_box, values["sample_rate"])
        self.mono_box = QCheckBox("Mono")
        self.mono_box.setChecked(values["mono"])

        self.bitrate = QComboBox()
        for kbps, label in bitrates:
            self.bitrate.addItem(label, kbps)
        self._select(self.bitrate, values["bitrate"])
        self.cut_fade = QDoubleSpinBox()
        self.cut_fade.setRange(0.0, 5000.0)
        self.cut_fade.setSingleStep(50.0)
        self.cut_fade.setSuffix(" ms")
        self.cut_fade.setValue(values["cut_fade_ms"])
        self.fade_out = QDoubleSpinBox()
        self.fade_out.setRange(0.0, 60.0)
        self.fade_out.setSuffix(" s")
        self.fade_out.setValue(values["end_fade_s"])
        self.night_box = QCheckBox("Quiet down loud parts")
        self.night_box.setChecked(values["night"])
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(-40.0, -6.0)
        self.threshold.setSuffix(" dB")
        self.threshold.setValue(values["threshold_db"])
        self.ceiling = QDoubleSpinBox()
        self.ceiling.setRange(-24.0, -0.5)
        self.ceiling.setSuffix(" dB")
        self.ceiling.setValue(values["ceiling_db"])

        form = QFormLayout()
        form.addRow(QLabel("<b>Folders</b>"))
        form.addRow("Export folder", self._path_row(
            self.export_edit, lambda: self._browse_dir(self.export_edit, "Choose export folder")))
        form.addRow("Finals folder", self._path_row(
            self.finals_edit, lambda: self._browse_dir(self.finals_edit, "Choose finals folder")))
        form.addRow("Cover image", self._path_row(
            self.cover_edit, self._browse_cover, self.cover_edit.clear))
        form.addRow(QLabel("<b>Recording</b>"))
        form.addRow("Sample rate", self.sr_box)
        form.addRow("", self.mono_box)
        form.addRow(QLabel("<b>Output</b>"))
        form.addRow("Bitrate", self.bitrate)
        form.addRow("Fade per cut", self.cut_fade)
        form.addRow("End fade", self.fade_out)
        form.addRow("", self.night_box)
        form.addRow("Threshold", self.threshold)
        form.addRow("Ceiling", self.ceiling)

        ok = QPushButton("OK")
        ok.setObjectName("primary")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(ok)
        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addLayout(buttons)

    @staticmethod
    def _select(combo, value):
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    def _path_row(self, edit, browse, clear=None):
        row = QHBoxLayout()
        row.addWidget(edit, 1)
        button = QPushButton("Browse...")
        button.clicked.connect(browse)
        row.addWidget(button)
        if clear is not None:
            x = QPushButton("\u00d7")
            x.setObjectName("tiny")
            x.setFixedWidth(26)
            x.clicked.connect(clear)
            row.addWidget(x)
        return row

    def _browse_dir(self, edit, title):
        path = QFileDialog.getExistingDirectory(self, title, edit.text())
        if path:
            edit.setText(path)

    def _browse_cover(self):
        start = os.path.dirname(self.cover_edit.text()) if self.cover_edit.text() else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose cover image", start, IMAGE_FILTER)
        if path:
            self.cover_edit.setText(path)

    def values(self):
        return {
            "export_dir": self.export_edit.text().strip(),
            "finals_dir": self.finals_edit.text().strip(),
            "cover": self.cover_edit.text().strip(),
            "sample_rate": self.sr_box.currentData(),
            "mono": self.mono_box.isChecked(),
            "bitrate": self.bitrate.currentData(),
            "cut_fade_ms": self.cut_fade.value(),
            "end_fade_s": self.fade_out.value(),
            "night": self.night_box.isChecked(),
            "threshold_db": self.threshold.value(),
            "ceiling_db": self.ceiling.value(),
        }

