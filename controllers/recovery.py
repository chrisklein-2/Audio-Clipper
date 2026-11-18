"""
recovery.py - RecoveryMixin: crash recovery for unsaved clips.

Each session file (session/rec_123.raw) gets a sidecar (session/rec_123.json)
describing the edit. Both are deleted on a clean exit, so anything still there
at startup means the app died with unsaved work.
"""

import glob
import json
import os
import time

from PySide6.QtCore import QTimer

from config import SESSION_DIR
from store import AudioStore
from editor import Keep, format_time
from ui.dialogs import confirm

AUTOSAVE_MS = 30000


# Path of the sidecar for a session file
def _meta_path(raw_path):
    return os.path.splitext(raw_path)[0] + ".json"


class RecoveryMixin:

    # Start the periodic autosave (call once at startup)
    def start_recovery_timer(self):
        self._recovery_timer = QTimer(self)
        self._recovery_timer.timeout.connect(self.save_recovery)
        self._recovery_timer.start(AUTOSAVE_MS)


    # Write the sidecar for the open clip.
    # While recording, pass raw_path / samplerate / channels (keeps are then
    # omitted, meaning "the whole file").
    def save_recovery(self, raw_path=None, samplerate=None, channels=None):
        if raw_path is None:
            if self.recorder is not None:
                return
            raw_path = self.session_path
            if (not raw_path or self.timeline.store is None
                    or self.timeline.duration() <= 0):
                return
            samplerate = self.timeline.samplerate()
            channels = self.timeline.channels()
            keeps = [[k.start, k.end, k.fade_in, k.fade_out] for k in self.timeline.keeps]
        else:
            keeps = None

        if not os.path.exists(raw_path):
            return
        data = {
            "version": 1,
            "raw": os.path.basename(raw_path),
            "samplerate": int(samplerate),
            "channels": int(channels),
            "keeps": keeps,
            "bookmarks": list(self.bookmarks),
            "clip_name": self.clip_name.text(),
            "unsaved": True,
            "saved_at": time.time(),
        }
        meta = _meta_path(raw_path)
        try:
            with open(meta + ".tmp", "w", encoding="utf-8") as handle:
                json.dump(data, handle)
            os.replace(meta + ".tmp", meta)
        except OSError:
            pass


    # Delete the sidecar for a session file (the raw file is handled elsewhere)
    def clear_recovery(self, raw_path):
        if not raw_path:
            return
        for path in (_meta_path(raw_path), _meta_path(raw_path) + ".tmp"):
            try:
                os.remove(path)
            except OSError:
                pass


    # Valid leftover sessions, newest first
    def _find_recoverable(self):
        found = []
        for meta_file in glob.glob(os.path.join(SESSION_DIR, "*.json")):
            try:
                with open(meta_file, encoding="utf-8") as handle:
                    data = json.load(handle)
                raw = os.path.join(SESSION_DIR, data["raw"])
                if (data.get("unsaved") and os.path.isfile(raw)
                        and os.path.getsize(raw) > 0):
                    data["raw_path"] = raw
                    found.append(data)
            except (OSError, ValueError, KeyError):
                continue
        found.sort(key=lambda d: d.get("saved_at", 0), reverse=True)
        return found


    # Delete every session file except the one being kept
    def _purge_sessions(self, keep_raw=None):
        for path in glob.glob(os.path.join(SESSION_DIR, "rec_*")):
            if keep_raw and os.path.splitext(path)[0] == os.path.splitext(keep_raw)[0]:
                continue
            try:
                os.remove(path)
            except OSError:
                pass


    # Called once after the window is shown
    def offer_recovery(self):
        if self.recorder is not None or self.timeline.duration() > 0:
            return
        found = self._find_recoverable()
        keep_raw = None
        if found:
            data = found[0]
            frame_bytes = 2 * data["channels"]
            seconds = os.path.getsize(data["raw_path"]) / frame_bytes / data["samplerate"]
            when = time.strftime("%H:%M on %d %b", time.localtime(data.get("saved_at", 0)))
            if confirm(
                self, "Recover unsaved clip?",
                f"Audio Clipper closed unexpectedly while a clip was open "
                f"({format_time(seconds)} of audio, last saved {when}).\n\n"
                f"Do you want to recover it?",
                "Recover", "Discard",
            ):
                keep_raw = data["raw_path"]
                self._recover(data)
        self._purge_sessions(keep_raw)


    # Re-open a leftover session with its cuts and bookmarks
    def _recover(self, data):
        raw = data["raw_path"]
        samplerate, channels = data["samplerate"], data["channels"]
        self.session_path = raw


        def work(report):
            store = AudioStore(raw, samplerate, channels)
            store.build_pyramid(report)
            return store


        def done(store):
            keeps = None
            if data.get("keeps"):
                limit = store.duration()
                keeps = [Keep(min(s, limit), min(e, limit), fi, fo)
                         for s, e, fi, fo in data["keeps"] if min(e, limit) > min(s, limit)]
            self.bookmarks[:] = data.get("bookmarks", [])
            self._show_store(store, data.get("clip_name") or None, keeps or None)
            self.unsaved = True
            self.update_actions()
            self.statusBar().showMessage("Recovered your unsaved clip.", 10000)


        self.run_task("Recovering", "Re-opening your unsaved clip...", work, done)