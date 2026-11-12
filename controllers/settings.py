"""controllers/settings.py - SettingsMixin: persisted settings + settings window."""
from PySide6.QtWidgets import QDialog

from audio_backends import SAMPLE_RATES
from processing import BITRATES
from ui.dialogs import SettingsDialog


def _select(combo, value):
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return


class SettingsMixin:

    def restore_settings(self):
        s = self.settings
        widgets = (self.sr_box, self.mono_box, self.bitrate, self.cut_fade,
                   self.fade_out, self.night_box, self.threshold, self.ceiling)
        for w in widgets:
            w.blockSignals(True)
        try:
            if s.contains("sample_rate"):
                _select(self.sr_box, s.value("sample_rate", type=int))
            if s.contains("mono"):
                self.mono_box.setChecked(s.value("mono", type=bool))
            if s.contains("bitrate"):
                _select(self.bitrate, s.value("bitrate", type=int))
            if s.contains("cut_fade_ms"):
                self.cut_fade.setValue(s.value("cut_fade_ms", type=float))
            if s.contains("end_fade_s"):
                self.fade_out.setValue(s.value("end_fade_s", type=float))
            if s.contains("night"):
                self.night_box.setChecked(s.value("night", type=bool))
            if s.contains("threshold_db"):
                self.threshold.setValue(s.value("threshold_db", type=float))
            if s.contains("ceiling_db"):
                self.ceiling.setValue(s.value("ceiling_db", type=float))
        finally:
            for w in widgets:
                w.blockSignals(False)
        self.wave.set_fade_ms(self.cut_fade.value())
        self.wave.set_end_fade(self.fade_out.value())
        self.check_rate_match()
        self.sr_box.currentIndexChanged.connect(self.save_settings)
        self.mono_box.toggled.connect(self.save_settings)
        self.bitrate.currentIndexChanged.connect(self.save_settings)
        self.cut_fade.valueChanged.connect(self.save_settings)
        self.fade_out.valueChanged.connect(self.save_settings)
        self.night_box.toggled.connect(self.save_settings)
        self.threshold.valueChanged.connect(self.save_settings)
        self.ceiling.valueChanged.connect(self.save_settings)

    def save_settings(self, *_):
        s = self.settings
        s.setValue("sample_rate", self.sr_box.currentData())
        s.setValue("mono", self.mono_box.isChecked())
        s.setValue("bitrate", self.bitrate.currentData())
        s.setValue("cut_fade_ms", self.cut_fade.value())
        s.setValue("end_fade_s", self.fade_out.value())
        s.setValue("night", self.night_box.isChecked())
        s.setValue("threshold_db", self.threshold.value())
        s.setValue("ceiling_db", self.ceiling.value())

    def open_settings(self):
        dlg = SettingsDialog({
            "export_dir": self.ensure_export_dir(),
            "finals_dir": self.ensure_finals_dir(),
            "cover": self.cover_path or "",
            "sample_rate": self.sr_box.currentData(),
            "mono": self.mono_box.isChecked(),
            "bitrate": self.bitrate.currentData(),
            "cut_fade_ms": self.cut_fade.value(),
            "end_fade_s": self.fade_out.value(),
            "night": self.night_box.isChecked(),
            "threshold_db": self.threshold.value(),
            "ceiling_db": self.ceiling.value(),
        }, SAMPLE_RATES, BITRATES, self)
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.values()
        if v["export_dir"] and v["export_dir"] != self.export_dir:
            self.export_dir = v["export_dir"]
            self.settings.setValue("export_dir", self.export_dir)
            self.ensure_export_dir()
        if v["finals_dir"] and v["finals_dir"] != self.finals_dir:
            self.finals_dir = v["finals_dir"]
            self.settings.setValue("finals_dir", self.finals_dir)
            self.ensure_finals_dir()
        if v["cover"] != (self.cover_path or ""):
            self.set_cover(v["cover"] or None)
        if self.recorder is None:            # locked while recording
            _select(self.sr_box, v["sample_rate"])
            self.mono_box.setChecked(v["mono"])
        _select(self.bitrate, v["bitrate"])
        self.cut_fade.setValue(v["cut_fade_ms"])
        self.fade_out.setValue(v["end_fade_s"])
        self.night_box.setChecked(v["night"])
        self.threshold.setValue(v["threshold_db"])
        self.ceiling.setValue(v["ceiling_db"])
        self.save_settings()
        self.update_actions()



    def on_fade_changed(self, value):
        self.wave.set_fade_ms(value)
        self.invalidate()

    def on_end_fade_changed(self, value):
        self.wave.set_end_fade(value)
        self.invalidate()