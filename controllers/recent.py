"""
recent.py - RecentMixin: the File > Open recent list.

Stored in QSettings as a JSON list of paths, newest first.
"""

import json
import os

MAX_RECENT = 10
SETTINGS_KEY = "recent_files"


class RecentMixin:

    # The saved list, newest first (may include files that no longer exist)
    def recent_files(self):
        try:
            paths = json.loads(self.settings.value(SETTINGS_KEY, "[]"))
        except (TypeError, ValueError):
            return []
        return [p for p in paths if isinstance(p, str)]


    def _save_recent(self, paths):
        self.settings.setValue(SETTINGS_KEY, json.dumps(paths))


    # Put a file at the top of the list (removing any older entry for it)
    def add_recent(self, path):
        path = os.path.normpath(os.path.abspath(path))
        key = os.path.normcase(path)
        paths = [p for p in self.recent_files() if os.path.normcase(p) != key]
        paths.insert(0, path)
        self._save_recent(paths[:MAX_RECENT])


    def clear_recent(self):
        self._save_recent([])


    # Fill the submenu; connected to its aboutToShow signal so it is always fresh
    def rebuild_recent_menu(self):
        menu = self.recent_menu
        menu.clear()

        saved = self.recent_files()
        paths = [p for p in saved if os.path.isfile(p)]
        if paths != saved:                  # forget files that were deleted
            self._save_recent(paths)

        if not paths:
            menu.addAction("(no recent files)").setEnabled(False)
            return

        for number, path in enumerate(paths, 1):
            name = os.path.basename(path).replace("&", "&&")
            label = f"&{number}  {name}" if number < 10 else f"{number}  {name}"
            action = menu.addAction(label)
            action.setToolTip(path)
            action.setStatusTip(path)
            action.triggered.connect(lambda checked=False, p=path: self.open_recent(p))

        menu.addSeparator()
        menu.addAction("Clear list", self.clear_recent)


    # Load a file chosen from the list
    def open_recent(self, path):
        if not os.path.isfile(path):
            self.statusBar().showMessage(
                f"{os.path.basename(path)} no longer exists.", 6000)
            return
        if self.confirm_discard("load a file"):
            self.load_path(path)