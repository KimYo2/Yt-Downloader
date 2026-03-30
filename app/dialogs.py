"""Dialog windows for YtDownloader application."""

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from .utils import runtime_base_dir


class SettingsDialog(QDialog):
    """Settings dialog for configuring application preferences."""

    def __init__(self, parent: QWidget, settings: dict) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(520, 260)

        self.folder_input = QLineEdit(settings.get("default_download_dir", ""))
        self.popup_check = QCheckBox("Show success popup")
        self.popup_check.setChecked(bool(settings.get("show_success_popup", True)))
        self.auto_analyze_check = QCheckBox("Enable auto analyze by default")
        self.auto_analyze_check.setChecked(bool(settings.get("auto_analyze", False)))
        self.auto_start_queue_check = QCheckBox("Auto start queue when adding job")
        self.auto_start_queue_check.setChecked(bool(settings.get("auto_start_queue", True)))
        self.playlist_default_check = QCheckBox("Download playlist by default")
        self.playlist_default_check.setChecked(bool(settings.get("default_download_playlist", False)))
        self.cookies_browser_combo = QComboBox()
        self.cookies_browser_combo.addItems(["none", "chrome", "edge", "firefox", "brave", "opera", "vivaldi", "safari"])
        self.cookies_browser_combo.setCurrentText(str(settings.get("cookies_from_browser", "none")).lower())
        self.cookies_file_input = QLineEdit(str(settings.get("cookies_file", "")))
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 5)
        self.retry_spin.setValue(int(settings.get("max_retries", 2)))

        root = QVBoxLayout(self)
        form = QFormLayout()

        folder_row = QHBoxLayout()
        browse_btn = QPushButton("Browse")
        browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(browse_btn)

        form.addRow("Default folder", folder_row)
        form.addRow("Max retries", self.retry_spin)
        form.addRow("Cookies from browser", self.cookies_browser_combo)
        cookies_row = QHBoxLayout()
        cookies_browse_btn = QPushButton("Browse")
        cookies_browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        cookies_browse_btn.clicked.connect(self._browse_cookies_file)
        cookies_row.addWidget(self.cookies_file_input)
        cookies_row.addWidget(cookies_browse_btn)
        form.addRow("Cookies file (optional)", cookies_row)
        form.addRow("", self.popup_check)
        form.addRow("", self.auto_analyze_check)
        form.addRow("", self.auto_start_queue_check)
        form.addRow("", self.playlist_default_check)
        root.addLayout(form)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save")
        cancel_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
        save_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        action_row.addWidget(cancel_btn)
        action_row.addWidget(save_btn)
        root.addLayout(action_row)

    def _browse_folder(self) -> None:
        current = self.folder_input.text().strip() or str(Path.home() / "Downloads")
        folder = QFileDialog.getExistingDirectory(self, "Select Default Folder", current)
        if folder:
            self.folder_input.setText(folder)

    def _browse_cookies_file(self) -> None:
        current = self.cookies_file_input.text().strip() or str(runtime_base_dir())
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookies File",
            current,
            "Cookies file (*.txt *.sqlite *.db);;All files (*.*)",
        )
        if filename:
            self.cookies_file_input.setText(filename)

    def get_settings(self) -> dict:
        """Get settings from dialog inputs."""
        return {
            "default_download_dir": self.folder_input.text().strip() or str(Path.home() / "Downloads"),
            "show_success_popup": self.popup_check.isChecked(),
            "auto_analyze": self.auto_analyze_check.isChecked(),
            "auto_start_queue": self.auto_start_queue_check.isChecked(),
            "default_download_playlist": self.playlist_default_check.isChecked(),
            "cookies_from_browser": self.cookies_browser_combo.currentText().strip().lower() or "none",
            "cookies_file": self.cookies_file_input.text().strip(),
            "max_retries": int(self.retry_spin.value()),
        }
