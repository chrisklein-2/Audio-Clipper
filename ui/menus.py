""" menus.py - MenuMixin: builds the menu bar and connects the actions to the main window. """

from .dialogs import HelpDialog
from utils import reveal_folder

class MenuMixin:    
    
    def _build_menu_bar(self):

        bar = self.menuBar()

#------------------ File Menu ---------------------------        
        file_menu = bar.addMenu("File")
        file_menu.addAction("New recording", self.new_recording, "Ctrl+N")
        file_menu.addSeparator()
        file_menu.addAction("Load audio / video file...", self.load_file, "Ctrl+O")
        self.recent_menu = file_menu.addMenu("Open recent")
        self.recent_menu.setToolTipsVisible(True)
        self.recent_menu.aboutToShow.connect(self.rebuild_recent_menu)
        file_menu.addAction("Append audio file...", self.append_file)
        file_menu.addAction("Join audio files...", self.join_files, "Ctrl+J")
        file_menu.addSeparator()
        file_menu.addAction(self.act_export)
        file_menu.addAction("Export as...", self.do_export_as, "Ctrl+Shift+E")
        file_menu.addAction(self.act_finalize)
        file_menu.addAction("Move last export to finals", self.move_to_finals)
        file_menu.addAction(self.act_send)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, "Ctrl+Q")


# ---------------- Edit Menu ---------------------------
        edit_menu = bar.addMenu("Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_mark_in)
        edit_menu.addAction(self.act_mark_out)
        edit_menu.addAction(self.act_selall)
        edit_menu.addAction(self.act_deselect)        
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_delete)
        edit_menu.addAction(self.act_restore)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_trim)
        edit_menu.addAction(self.act_piece_fades)
        edit_menu.addAction(self.act_reset)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_bookmark)
        edit_menu.addAction(self.act_rm_bookmark)
        edit_menu.addAction(self.act_prev_bookmark)
        edit_menu.addAction(self.act_next_bookmark)
        edit_menu.addAction(self.act_clear_bookmarks)

#------------------ View Menu ---------------------------
        view_menu = bar.addMenu("View")
        view_menu.addAction(self.act_fit)
        view_menu.addAction(self.act_zoomsel)
        view_menu.addSeparator()
        view_menu.addAction(self.act_pieces)

#------------------ Settings Menu ---------------------------
        settings_menu = bar.addMenu("Settings")
        settings_menu.addAction("Select audio source...", self.choose_source, "Ctrl+I")
        settings_menu.addSeparator()
        settings_menu.addAction("Set export folder...", self.choose_export_dir)
        settings_menu.addAction("Set finals folder...", self.choose_finals_dir)
        settings_menu.addAction("Open export folder",
                     lambda: reveal_folder(self.ensure_export_dir()))
        settings_menu.addAction("Open finals folder",
                     lambda: reveal_folder(self.ensure_finals_dir()))
        settings_menu.addSeparator()
        settings_menu.addAction("Choose cover image...", self.choose_cover)
        settings_menu.addSeparator()
        settings_menu.addAction("All settings...", self.open_settings)

        bar.addMenu("Help").addAction(self.act_help)

    def show_help(self):
        HelpDialog(self).exec()
