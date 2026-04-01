"""Download progress window for YtDownloader."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from .models import DownloadJob
from .utils import human_bytes


class DownloadProgressWindow(QDialog):
    """Dedicated window showing download progress for a single job."""

    proceed_to_next = Signal(bool)

    def __init__(self, parent, job: DownloadJob, on_cancel_callback) -> None:
        super().__init__(parent)
        self.setWindowTitle("Downloading...")
        self.setFixedSize(500, 330)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self._on_cancel = on_cancel_callback
        self._download_complete = False
        self._properly_finished = False
        self._countdown_timer: QTimer | None = None
        self._countdown_remaining = 3

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        self.title_label = QLabel("Downloading")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(self.title_label)

        self.video_title_label = QLabel(job.title)
        self.video_title_label.setObjectName("ProgressTitle")
        self.video_title_label.setWordWrap(True)
        self.video_title_label.setStyleSheet("color: #93c5fd; font-weight: 600;")
        layout.addWidget(self.video_title_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("ProgressStatus")
        layout.addWidget(self.status_label)

        self.bytes_label = QLabel("")
        layout.addWidget(self.bytes_label)

        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")
        layout.addWidget(self.countdown_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #334155;")
        layout.addWidget(separator)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.setStyleSheet(
            "QPushButton { background: #dc2626; color: white; border: none; border-radius: 8px; padding: 8px 14px; font-weight: 600; }"
            "QPushButton:hover { background: #b91c1c; }"
            "QPushButton:disabled { background: #475569; color: #cbd5e1; }"
        )
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.setStyleSheet(
            "QDialog { background: #0f172a; color: #e2e8f0; font-size: 13px; }"
            "QProgressBar { border: 1px solid #334155; border-radius: 8px; text-align: center; background: #1e293b; }"
            "QProgressBar::chunk { background: #22c55e; border-radius: 8px; }"
            "QLabel { color: #e2e8f0; }"
        )

    def _on_cancel_clicked(self) -> None:
        self._on_cancel()
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling...")

    def update_progress(self, percent: float, status_msg: str, downloaded_bytes: int, total_bytes: int) -> None:
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(status_msg)
        dl_text = human_bytes(downloaded_bytes)
        total_text = human_bytes(total_bytes) if total_bytes > 0 else "Unknown size"
        self.bytes_label.setText(f"{dl_text} / {total_text}")

    def set_title(self, title: str) -> None:
        self.video_title_label.setText(title)

    def mark_done(self) -> None:
        self._download_complete = True
        self.progress_bar.setValue(100)
        self.title_label.setText("\u2713 Download Complete")
        self.cancel_btn.setText("Next Now")
        self.cancel_btn.setEnabled(True)
        try:
            self.cancel_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self.cancel_btn.clicked.connect(self._skip_countdown)
        self._start_countdown()

    def _start_countdown(self) -> None:
        self._countdown_remaining = 3
        self._update_countdown_label()
        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_timer.start()

    def _countdown_tick(self) -> None:
        self._countdown_remaining -= 1
        self._update_countdown_label()
        if self._countdown_remaining <= 0:
            self._finish_transition()

    def _update_countdown_label(self) -> None:
        n = self._countdown_remaining
        self.countdown_label.setText(
            f"Next download starts in {n}s\u2026" if n > 0 else "Starting next\u2026"
        )

    def _skip_countdown(self) -> None:
        if self._countdown_timer is not None:
            self._countdown_timer.stop()
        self._finish_transition()

    def _finish_transition(self) -> None:
        if self._countdown_timer is not None:
            self._countdown_timer.stop()
        self._properly_finished = True
        self.proceed_to_next.emit(True)
        self.close()

    def mark_error(self, message: str) -> None:
        self._download_complete = True
        self.title_label.setText("\u2717 Download Failed")
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #334155; border-radius: 8px; text-align: center; background: #1e293b; }"
            "QProgressBar::chunk { background: #ef4444; border-radius: 8px; }"
        )
        self.status_label.setText(message)
        self.cancel_btn.setText("Close")
        self.cancel_btn.setEnabled(True)
        try:
            self.cancel_btn.clicked.disconnect()
        except RuntimeError:
            pass
        self.cancel_btn.clicked.connect(self.close)

    def mark_cancelled(self) -> None:
        self._download_complete = True
        self.title_label.setText("\u2298 Cancelled")
        self.cancel_btn.setEnabled(False)
        QTimer.singleShot(1000, self.close)

    def closeEvent(self, event) -> None:
        if self._countdown_timer is not None:
            self._countdown_timer.stop()
        if not self._properly_finished:
            if self._download_complete:
                # Window closing after mark_done countdown, mark_error, or mark_cancelled
                self.proceed_to_next.emit(True)
            else:
                # User force-closed window while download was still running
                self._on_cancel()
                self.proceed_to_next.emit(False)
        super().closeEvent(event)
