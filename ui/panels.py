""" panels.py - PanelsMixin: builds the main window's panels and connects the actions to the main window. """
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QScrollBar, QSizePolicy, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt
from waveform import WaveformView
from .widgets import (
    sep, make_button, make_line_edit, add_widgets, add_action_buttons,
)
from audio_backends import SAMPLE_RATES



class PanelsMixin:

    # ---- UI build -------------------------------------------------------

    def _build_top_row(self):


        # record button
        self.rec_btn = make_button(
            "Record", self.toggle_record,
            object_name="record", checkable=True, min_width=115)


        # stop recording button
        self.stop_rec_btn = make_button(
            "Stop rec", self.stop_record,
            tooltip="Finish recording and load for editing",
            min_width=80, enabled=False)


        # bookmark button
        self.mark_btn = make_button(
            "Mark", self.add_bookmark,
            tooltip="Drop a bookmark at the current time   [Ctrl+B]",
            min_width=60, enabled=False)


        # zoom button
        self.live_zoom_btn = make_button(
            "View: last 8 s",
            tooltip=("While recording: switch between the whole recording so far "
                     "and only the last 8 s"),
            min_width=100, checkable=True, checked=True, enabled=False,
            on_toggled=lambda on: self.live_zoom_btn.setText(
                "View: last 8 s" if on else "View: whole"))


        # source button
        self.source_btn = make_button(
            "Source: none", self.choose_source,
            tooltip="Click to choose what to record   [Ctrl+I]",
            min_width=160)


        # clip name box
        self.clip_name = make_line_edit(
            "clip",
            placeholder="Clip name (used as the filename and title)",
            tooltip="Filename and metadata title on export.",
            min_width=100)


        ## assemble the row
        self.sr_box = QComboBox()
        for rate, label in SAMPLE_RATES:
            self.sr_box.addItem(label, rate)
        self.sr_box.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.sr_box.setMinimumContentsLength(10)
        self.sr_box.view().setMinimumWidth(260)
        self.sr_box.setToolTip(
            "Match this to your device's rate in Windows Sound\n"
            "settings. A mismatch forces a resample."
        )
        self.sr_box.currentIndexChanged.connect(self.check_rate_match)


        # mono checkbox
        self.mono_box = QCheckBox("Mono")
        self.mono_box.setToolTip("Halves disk and file size — ideal for podcasts.")
        record_separator = sep()
        self._record_only = [self.rec_btn, self.stop_rec_btn, self.live_zoom_btn,
                             self.source_btn, record_separator, self.sr_box, self.mono_box]


        # add the widgets (None = separator, (widget, 1) = stretch factor 1)
        row = QHBoxLayout()
        add_widgets(
            row,
            self.rec_btn, self.stop_rec_btn, self.mark_btn,
            self.live_zoom_btn, self.source_btn, record_separator,
            self.sr_box, self.mono_box, None,
            QLabel("Name:"), (self.clip_name, 1),
        )
        return row



    def _build_middle(self):


        # create the wave form
        self.wave = WaveformView()
        self.wave.set_timeline(self.timeline)
        self.wave.selectionChanged.connect(self.update_actions)
        self.wave.playheadMoved.connect(self.on_playhead_moved)
        self.wave.viewChanged.connect(self.sync_scrollbar)
        self.wave.blockSelected.connect(self.on_block_selected)
        self.wave.drop_filter = self.can_accept_drop
        self.wave.filesDropped.connect(self.drop_files)
        self.wave.context_actions = [
            self.act_mark_in, self.act_mark_out, None,
            self.act_delete, self.act_restore, None,
            self.act_selall, self.act_zoomsel, self.act_fit,
            None, self.act_undo, self.act_redo, self.act_piece_fades, None,
            self.act_bookmark, self.act_rm_bookmark,
        ]


        # side bar on the right that collapses
        self.collapse_btn = make_button(
            "\u25c0",
            tooltip="Show / hide the kept pieces list  [Ctrl+L]",
            object_name="collapse", fixed_width=14,
            size_policy=(QSizePolicy.Fixed, QSizePolicy.Expanding),
            checkable=True, checked=True,
            on_toggled=self.act_pieces.setChecked)


        # list of kept pieces
        self.seg_list = QListWidget()
        self.seg_list.setToolTip("Click to jump, double-click to set this piece's fades.")
        self.seg_list.itemClicked.connect(self.on_piece_clicked)
        self.seg_list.itemDoubleClicked.connect(self.on_piece_double_clicked)


        self.pieces_panel = QWidget()
        self.pieces_panel.setFixedWidth(195)
        self.pieces_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)


        pieces_layout = QVBoxLayout(self.pieces_panel)
        pieces_layout.setContentsMargins(0, 0, 0, 0)
        pieces_layout.addWidget(QLabel("Kept pieces"))
        pieces_layout.addWidget(self.seg_list, 1)


        middle_row = QHBoxLayout()
        middle_row.addWidget(self.wave, 1)
        middle_row.addWidget(self.collapse_btn)
        middle_row.addWidget(self.pieces_panel)
        return middle_row


    def _build_nav_row(self):


        # horizontal scroll bar
        self.scroll = QScrollBar(Qt.Horizontal)
        self.scroll.setRange(0, 0)
        self.scroll.setToolTip("Pan the view when zoomed in")
        self.scroll.valueChanged.connect(self.on_scroll)


        # zoom out button
        self.zoom_out_btn = make_button(
            "\u2212",  # minus sign
            lambda: self.wave.zoom_out(),
            tooltip="Zoom out around the playhead   [-]",
            object_name="tiny", fixed_width=32)


        # zoom in button
        self.zoom_in_btn = make_button(
            "+",
            lambda: self.wave.zoom_in(),
            tooltip="Zoom in around the playhead   [+]",
            object_name="tiny", fixed_width=32)


        # fit button
        self.fit_btn = make_button(
            "Fit",
            lambda: self.wave.zoom_fit(),
            tooltip="Zoom out to the whole recording   [Ctrl+0]")


        # go to time box and button
        self.goto_edit = make_line_edit(
            placeholder="4:20",
            tooltip="Jump to a time: 4:20, 1:04:20, 4m20s or 260\nPress Enter.",
            fixed_width=110,
            on_return=self.do_goto)
        goto_btn = make_button("Go", self.do_goto)


        # add the widgets
        row = QHBoxLayout()
        add_widgets(
            row,
            (self.scroll, 1), self.zoom_out_btn, self.zoom_in_btn,
            self.fit_btn, None,
            QLabel("Go to"), self.goto_edit, goto_btn,
        )
        return row


    def _build_edit_group(self):
        edit_group = QGroupBox("EDIT")
        edit_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        row = QHBoxLayout(edit_group)

        # buttons built from actions (None = separator)
        add_action_buttons(row, (
            self.act_undo, self.act_redo, None, self.act_mark_in,
            self.act_mark_out, self.act_selall, None, self.act_delete,
            self.act_restore, None, self.act_trim, self.act_reset,
        ))
        row.addStretch(1)
        return edit_group

    def _build_hint(self):
        hint_label = QLabel(
            "Drag = select  \u2022  Ruler = playhead  \u2022  [ ] = mark in/out  "
            "\u2022  Del = delete  \u2022  Space = from playhead  \u2022  "
            "Ctrl+B = bookmark  \u2022  + / - = zoom  \u2022  Ctrl+Z = undo  "
            "\u2022  F1 = help"
        )
        hint_label.setObjectName("hint")
        hint_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        hint_label.setFixedHeight(hint_label.sizeHint().height())
        return hint_label