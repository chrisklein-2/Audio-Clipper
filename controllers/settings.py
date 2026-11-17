"""controllers/settings.py - SettingsMixin: persisted settings + settings window."""
from PySide6.QtWidgets import QDialog

from audio_backends import SAMPLE_RATES
from processing import BITRATES
from ui.dialogs import SettingsDialog


def select_combo_value(combo, value):
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return


class SettingsMixin:

    def restore_settings(self):
        settings = self.settings
        widgets = (self.sr_box, self.mono_box, self.bitrate, self.cut_fade,
                   self.fade_out, self.night_box, self.threshold, self.ceiling)
        for widget in widgets:
            widget.blockSignals(True)
        try:
            if settings.contains("sample_rate"):
                select_combo_value(self.sr_box, settings.value("sample_rate", type=int))
            if settings.contains("mono"):
                self.mono_box.setChecked(settings.value("mono", type=bool))
            if settings.contains("bitrate"):
                select_combo_value(self.bitrate, settings.value("bitrate", type=int))
            if settings.contains("cut_fade_ms"):
                self.cut_fade.setValue(settings.value("cut_fade_ms", type=float))
            if settings.contains("end_fade_s"):
                self.fade_out.setValue(settings.value("end_fade_s", type=float))
            if settings.contains("night"):
                self.night_box.setChecked(settings.value("night", type=bool))
            if settings.contains("threshold_db"):
                self.threshold.setValue(settings.value("threshold_db", type=float))
            if settings.contains("ceiling_db"):
                self.ceiling.setValue(settings.value("ceiling_db", type=float))
        finally:
            for widget in widgets:
                widget.blockSignals(False)
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
        settings = self.settings
        settings.setValue("sample_rate", self.sr_box.currentData())
        settings.setValue("mono", self.mono_box.isChecked())
        settings.setValue("bitrate", self.bitrate.currentData())
        settings.setValue("cut_fade_ms", self.cut_fade.value())
        settings.setValue("end_fade_s", self.fade_out.value())
        settings.setValue("night", self.night_box.isChecked())
        settings.setValue("threshold_db", self.threshold.value())
        settings.setValue("ceiling_db", self.ceiling.value())

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
        values = dlg.values()
        if values["export_dir"] and values["export_dir"] != self.export_dir:
            self.export_dir = values["export_dir"]
            self.settings.setValue("export_dir", self.export_dir)
            self.ensure_export_dir()
        if values["finals_dir"] and values["finals_dir"] != self.finals_dir:
            self.finals_dir = values["finals_dir"]
            self.settings.setValue("finals_dir", self.finals_dir)
            self.ensure_finals_dir()
        if values["cover"] != (self.cover_path or ""):
            self.set_cover(values["cover"] or None)
        if self.recorder is None:            # locked while recording
            select_combo_value(self.sr_box, values["sample_rate"])
            self.mono_box.setChecked(values["mono"])
        select_combo_value(self.bitrate, values["bitrate"])
        self.cut_fade.setValue(values["cut_fade_ms"])
        self.fade_out.setValue(values["end_fade_s"])
        self.night_box.setChecked(values["night"])
        self.threshold.setValue(values["threshold_db"])
        self.ceiling.setValue(values["ceiling_db"])
        self.save_settings()
        self.update_actions()



    def on_fade_changed(self, value):
        self.wave.set_fade_ms(value)
        self.invalidate()

    def on_end_fade_changed(self, value):
        self.wave.set_end_fade(value)
        self.invalidate()