"""
fileio.py - FileIOMixin: session management, load, append, join.

Mixed into MainWindow.
"""

import os
import time

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from store import AudioStore                                      
from editor import Keep, format_time                                  
from processing import append_decoded, decode_to_raw                   
from config import LOAD_EXTS, LOAD_FILTER, SESSION_DIR                       
from ui.dialogs import JoinDialog, confirm                                       
from utils import mbytes                                            

class FileIOMixin:

# ---- group session management ----------------------------------------------

    def new_session_path(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        return os.path.join(SESSION_DIR, f"rec_{int(time.time())}.raw")

    def drop_session(self):
        if self.timeline.store is not None:
            self.timeline.store.close()
        if self.session_path and os.path.exists(self.session_path):
            try:
                os.remove(self.session_path)
            except OSError:
                pass
        self.session_path = None

    def reset_to_record_screen(self):
        self.stop_playback()
        self.drop_session()
        self.timeline.set_store(None)
        self.bookmarks.clear()
        self.wave.set_bookmarks(self.bookmarks)
        self.wave.set_timeline(self.timeline)
        self.unsaved = False
        self.refresh_pieces()
        self.sync_scrollbar()
        self.statusBar().clearMessage()        
        self.set_mode("record")
        self.update_actions()

    def new_recording(self):
        """File menu: scrap the current clip and go to the record screen."""
        if self.confirm_discard("start a new recording"):
            self.reset_to_record_screen()

    def confirm_discard(self, verb="start a new recording"):
        if self.recorder is not None:
            if not confirm(
                self, "Recording in progress",
                f"A recording is in progress and has NOT been saved.\n\n"
                f"If you {verb} now, it will be discarded.",
                "Discard recording", "Keep recording",
            ):
                return False
            self.abort_record()
            return True
        if self.timeline.duration() <= 0:
            return True
        if self.unsaved:
            return confirm(
                self, "Discard current clip?",
                f"The current clip has NOT been exported.\n\n"
                f"If you {verb} now, those edits are gone for good.",
                "Discard without saving", "Cancel",
            )
        return confirm(
            self, "Replace current clip?",
            "This will replace the current clip.\n\n"
            "(Your last export is safe on disk.)",
            "Replace clip", "Cancel",
        )
# ---- loading ----------------------------------------------

    def _show_store(self, store, name_hint=None, keeps=None):
        self.timeline.set_store(store, keeps)
        self.wave.set_timeline(self.timeline)
        self.wave.set_fade_ms(self.cut_fade.value())
        self.wave.set_end_fade(self.fade_out.value())
        self.wave.set_bookmarks(self.bookmarks)
        if name_hint:
            self.clip_name.setText(name_hint)
        self.last_export = None
        self.invalidate()
        self.sync_scrollbar()
        self.statusBar().showMessage(
            f"{format_time(store.duration())} on disk "
            f"({mbytes(os.path.getsize(store.path))}), overview "
            f"{mbytes(store.pyramid_bytes())} in RAM", 10000)
        self.set_mode("edit")
        

    def load_file(self):
        if not self.confirm_discard("load a file"):
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open audio / video", self.ensure_export_dir(), LOAD_FILTER
        )
        if path:
            self.load_path(path)

    def load_path(self, path):
        self.stop_playback()
        self.drop_session()
        self.bookmarks.clear()
        raw = self.new_session_path()
        self.session_path = raw

        def work(report):
            _, rate, chans = decode_to_raw(path, raw)
            store = AudioStore(raw, rate, chans)
            store.build_pyramid(report)
            return store

        def done(store):
            self._show_store(store, os.path.splitext(os.path.basename(path))[0])
            self.unsaved = False
            self.update_actions()

        self.run_task("Loading", f"Decoding {os.path.basename(path)}...", work, done)

    def append_file(self):
        if self.timeline.duration() <= 0:
            self.load_file()
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Append audio / video to the end",
            self.ensure_export_dir(), LOAD_FILTER,
        )
        if not path:
            return
        self.stop_playback()
        old_keeps = [k.copy() for k in self.timeline.keeps]
        old_end = self.timeline.duration()
        raw = self.session_path
        rate = self.timeline.samplerate()
        chans = self.timeline.channels()
        self.timeline.store.close()

        def work(report):
            append_decoded(path, raw, rate, chans)
            store = AudioStore(raw, rate, chans)
            store.build_pyramid(report)
            return store

        def done(store):
            keeps = [k.copy() for k in old_keeps]
            keeps.append(Keep(old_end, store.duration()))
            self._show_store(store, keeps=keeps)
            self.statusBar().showMessage(
                f"Appended {os.path.basename(path)} - total "
                f"{format_time(store.duration())}",
                10000,
            )
        def failed(_msg):
            def rebuild(report):
                s = AudioStore(raw, rate, chans)
                s.build_pyramid(report)
                return s
            self.run_task("Restoring", "Re-opening the recording...", rebuild,
                          lambda s: self._show_store(
                              s,keeps=[k.copy() for k in old_keeps]))

        self.run_task("Appending",
                      f"Decoding and joining {os.path.basename(path)}...",
                      work, done, failed)


    def join_files(self):
        if not self.confirm_discard("join files"):
            return
        dlg = JoinDialog(self.ensure_export_dir(), self)
        if dlg.exec() != QDialog.Accepted:
            return
        paths = dlg.files()
        if not paths:
            return
        self.stop_playback()
        self.drop_session()
        self.bookmarks.clear()
        raw = self.new_session_path()
        self.session_path = raw

        def work(report):
            frames, rate, chans = decode_to_raw(paths[0], raw)
            bounds = [frames]
            for p in paths[1:]:
                bounds.append(append_decoded(p, raw, rate, chans))
            store = AudioStore(raw, rate, chans)
            store.build_pyramid(report)
            return store, bounds, rate

        def done(result):
            store, bounds, rate = result
            keeps, start = [], 0
            for end in bounds:
                if end > start:
                    keeps.append(Keep(start / rate, end / rate))
                start = end
            self._show_store(
                store,
                os.path.splitext(os.path.basename(paths[0]))[0] + "_joined",
                keeps,
            )
            self.statusBar().showMessage(
                f"Joined {len(paths)} files - {format_time(store.duration())}", 10000
            )

        self.run_task(
            "Joining", f"Decoding and joining {len(paths)} files...", work, done
        )

# ---- drag and drop ----------------------------------------------

    def drop_path(self, mime):
        """The single approved audio file in a drop, or None."""
        if not mime.hasUrls():
            return None
        urls = mime.urls()
        if len(urls) != 1 or not urls[0].isLocalFile():
            return None
        path = urls[0].toLocalFile()
        if os.path.splitext(path)[1].lower() not in LOAD_EXTS:
            return None
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            return None
        return path

    def can_accept_drop(self, mime):
        return (self.mode == "record" and self.recorder is None
                and self.drop_path(mime) is not None)

    def handle_drop(self, mime):
        path = self.drop_path(mime)
        if path is None or self.mode != "record" or self.recorder is not None:
            self.statusBar().showMessage(
                "Drop a single audio file (" + " ".join(LOAD_EXTS) + ")", 6000)
            return
        if self.confirm_discard("load a file"):
            self.load_path(path)

