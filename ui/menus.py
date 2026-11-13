""" menus.py - MenuMixin: builds the menu bar and connects the actions to the main window. """

from .dialogs import HelpDialog
from utils import reveal_folder

class MenuMixin:    
    
    def _build_menu_bar(self):

        bar = self.menuBar()

#------------------ File Menu ---------------------------        
        fm = bar.addMenu("File")
        fm.addAction("New recording", self.new_recording, "Ctrl+N")
        fm.addSeparator()
        fm.addAction("Load audio / video file...", self.load_file, "Ctrl+O")
        fm.addAction("Append audio file...", self.append_file)
        fm.addAction("Join audio files...", self.join_files, "Ctrl+J")
        fm.addSeparator()
        fm.addAction(self.act_export)
        fm.addAction("Export as...", self.do_export_as, "Ctrl+Shift+E")
        fm.addAction(self.act_finalize)
        fm.addAction("Move last export to finals", self.move_to_finals)
        fm.addAction(self.act_send)
        fm.addSeparator()
        fm.addAction("Quit", self.close, "Ctrl+Q")


# ---------------- Edit Menu ---------------------------
        em = bar.addMenu("Edit")
        em.addAction(self.act_undo)
        em.addAction(self.act_redo)
        em.addSeparator()
        em.addAction(self.act_mark_in)
        em.addAction(self.act_mark_out)
        em.addAction(self.act_selall)
        em.addAction(self.act_deselect)        
        em.addSeparator()
        em.addAction(self.act_delete)
        em.addAction(self.act_restore)
        em.addSeparator()
        em.addAction(self.act_trim)
        em.addAction(self.act_piece_fades)
        em.addAction(self.act_reset)
        em.addSeparator()
        em.addAction(self.act_bookmark)
        em.addAction(self.act_rm_bookmark)
        em.addAction(self.act_prev_bookmark)
        em.addAction(self.act_next_bookmark)
        em.addAction(self.act_clear_bookmarks)

#------------------ View Menu ---------------------------
        vm = bar.addMenu("View")
        vm.addAction(self.act_fit)
        vm.addAction(self.act_zoomsel)
        vm.addSeparator()
        vm.addAction(self.act_pieces)

#------------------ Settings Menu ---------------------------
        sm = bar.addMenu("Settings")
        sm.addAction("Select audio source...", self.choose_source, "Ctrl+I")
        sm.addSeparator()
        sm.addAction("Set export folder...", self.choose_export_dir)
        sm.addAction("Set finals folder...", self.choose_finals_dir)
        sm.addAction("Open export folder",
                     lambda: reveal_folder(self.ensure_export_dir()))
        sm.addAction("Open finals folder",
                     lambda: reveal_folder(self.ensure_finals_dir()))
        sm.addSeparator()
        sm.addAction("Choose cover image...", self.choose_cover)
        sm.addSeparator()
        sm.addAction("All settings...", self.open_settings)

        bar.addMenu("Help").addAction(self.act_help)

    def show_help(self):
        HelpDialog(self).exec()
