"""
fileio.py - FileIOMixin: session management, load, append, insert, join.


Mixed into MainWindow.
"""


import os
import time


from PySide6.QtWidgets import QDialog, QFileDialog
from store import AudioStore
from editor import Keep, format_time
from editor.splice import insert_into_keeps
from processing import append_decoded, decode_to_raw, insert_decoded
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

    # File menu: scrap the current clip and go to the record screen
    def new_recording(self):
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
        raw_path = self.new_session_path()
        self.session_path = raw_path


        def work(report):
            _, samplerate, channels = decode_to_raw(path, raw_path)
            store = AudioStore(raw_path, samplerate, channels)
            store.build_pyramid(report)
            return store


        def done(store):
            self._show_store(store, os.path.splitext(os.path.basename(path))[0])
            self.unsaved = False
            self.add_recent(path)            
            self.update_actions()


        self.run_task("Loading", f"Decoding {os.path.basename(path)}...", work, done)


# ---- append / insert ----------------------------------------------


    # File menu: pick one or more files and add them to the end
    def append_file(self):
        if self.timeline.duration() <= 0:
            self.load_file()
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Append audio / video to the end",
            self.ensure_export_dir(), LOAD_FILTER,
        )
        if paths:
            self.insert_files(paths)


    # Put one or more files into the open clip.
    # at_seconds = where in the clip; None (or past the end) = append to the end.
    def insert_files(self, paths, at_seconds=None):
        paths = list(paths)
        if not paths:
            return
        if self.timeline.store is None or self.timeline.duration() <= 0:
            self.join_paths(paths)
            return

        self.stop_playback()
        old_keeps = [k.copy() for k in self.timeline.keeps]
        raw_path = self.session_path
        samplerate = self.timeline.samplerate()
        channels = self.timeline.channels()
        frame_bytes = 2 * channels
        old_frames = self.timeline.store.frames()

        # Work out the insertion point in frames
        if at_seconds is None:
            at_frame = old_frames
        else:
            at_frame = max(0, min(old_frames, int(round(at_seconds * samplerate))))
        at_end = at_frame >= old_frames
        self.timeline.store.close()


        # Background: decode and write the new raw file, rebuild the overview
        def work(report):
            if at_end:
                # Fast path: just add to the end of the file
                lengths, start = [], old_frames
                for p in paths:
                    end = append_decoded(p, raw_path, samplerate, channels)
                    lengths.append(end - start)
                    start = end
            else:
                lengths = insert_decoded(paths, raw_path, at_frame, samplerate, channels)
            store = AudioStore(raw_path, samplerate, channels)
            store.build_pyramid(report)
            return store, lengths


        # Back on the GUI thread: rebuild the keeps and show the result
        def done(result):
            store, lengths = result
            seconds = [n / samplerate for n in lengths]
            at = at_frame / samplerate
            keeps = insert_into_keeps(old_keeps, at, seconds)

            # Bookmarks after the insertion point move later by the same amount
            if not at_end:
                shift = sum(seconds)
                self.bookmarks[:] = [b + shift if b >= at else b for b in self.bookmarks]

            self._show_store(store, keeps=keeps)
            self.unsaved = True
            self.update_actions()

            # Show what was inserted: select it and park the playhead at its start
            if not at_end:
                self.wave.set_selection(at, at + sum(seconds))
                self.wave.goto(at)

            names = (os.path.basename(paths[0]) if len(paths) == 1
                     else f"{len(paths)} files")
            where = "end" if at_end else format_time(at)
            self.statusBar().showMessage(
                f"Added {names} at {where} - total "
                f"{format_time(store.duration())}", 10000)


        # Something went wrong: put the recording back as it was
        def failed(_msg):
            if at_end:
                try:
                    with open(raw_path, "r+b") as handle:
                        handle.truncate(old_frames * frame_bytes)
                except OSError:
                    pass

            def rebuild(report):
                s = AudioStore(raw_path, samplerate, channels)
                s.build_pyramid(report)
                return s

            def restored(s):
                self._show_store(s, keeps=[k.copy() for k in old_keeps])
                self.statusBar().showMessage(
                    "Could not add the file(s) - the clip was left as it was.", 10000)

            self.run_task("Restoring", "Re-opening the recording...", rebuild, restored)


        self.run_task("Adding audio",
                      f"Decoding and inserting {len(paths)} file(s)...",
                      work, done, failed)


# ---- join ----------------------------------------------


    # File menu: pick files in a dialog, then join them into a new clip
    def join_files(self):
        if not self.confirm_discard("join files"):
            return
        dlg = JoinDialog(self.ensure_export_dir(), self)
        if dlg.exec() != QDialog.Accepted:
            return
        paths = dlg.files()
        if paths:
            self.join_paths(paths)


    # Join a list of files, in order, into a new clip (no confirmation here)
    def join_paths(self, paths):
        self.stop_playback()
        self.drop_session()
        self.bookmarks.clear()
        raw_path = self.new_session_path()
        self.session_path = raw_path


        def work(report):
            frames, samplerate, channels = decode_to_raw(paths[0], raw_path)
            bounds = [frames]
            for p in paths[1:]:
                bounds.append(append_decoded(p, raw_path, samplerate, channels))
            store = AudioStore(raw_path, samplerate, channels)
            store.build_pyramid(report)
            return store, bounds, samplerate


        def done(result):
            store, bounds, samplerate = result
            keeps, start = [], 0
            for end in bounds:
                if end > start:
                    keeps.append(Keep(start / samplerate, end / samplerate))
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


    # Keep only real, non-empty audio files from a list of paths
    def valid_audio_paths(self, paths):
        good = []
        for path in paths:
            if (os.path.splitext(path)[1].lower() in LOAD_EXTS
                    and os.path.isfile(path) and os.path.getsize(path) > 0):
                good.append(path)
        return good


    # The usable audio files in a drop (empty list if none)
    def drop_paths(self, mime):
        if not mime.hasUrls():
            return []
        return self.valid_audio_paths(
            [u.toLocalFile() for u in mime.urls() if u.isLocalFile()])


    # Can a drop be accepted right now? (never while recording)
    def can_accept_drop(self, mime):
        return self.recorder is None and bool(self.drop_paths(mime))


    # Whole-window drop (no position): loads on the record screen, appends on the edit screen
    def handle_drop(self, mime, at_seconds=None):
        self.drop_files(self.drop_paths(mime), at_seconds)


    # Files dropped, optionally at a time in the clip (None or negative = the end)
    def drop_files(self, paths, at_seconds=None):
        paths = self.valid_audio_paths(paths)
        if not paths or self.recorder is not None:
            self.statusBar().showMessage(
                "Drop audio files (" + " ".join(LOAD_EXTS) + ")", 6000)
            return
        if at_seconds is not None and at_seconds < 0:
            at_seconds = None

        # Record screen: nothing open yet, so load (one file) or join (several)
        if self.mode == "record":
            if not self.confirm_discard("load a file"):
                return
            if len(paths) == 1:
                self.load_path(paths[0])
            else:
                self.join_paths(paths)
            return

        # Edit screen: put the files into the open clip
        self.insert_files(paths, at_seconds)