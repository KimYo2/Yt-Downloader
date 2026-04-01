"""Main application window for YtDownloader."""

import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import yt_dlp
from yt_dlp.utils import DownloadError
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from .dialogs import SettingsDialog
from .models import DownloadJob
from .progress_window import DownloadProgressWindow
from .utils import (
    _SilentYDLLogger,
    find_app_icon_path,
    human_bytes,
    default_download_dir,
    detect_ffmpeg_location,
    logger,
    runtime_base_dir,
    apply_cookie_settings,
    strip_cookie_settings,
    has_cookie_opts,
    is_cookie_copy_error,
    is_youtube_bot_check_error,
    apply_youtube_client_fallback,
)


class DownloaderWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Social Media Downloader Pro")
        self.resize(980, 650)
        icon_path = find_app_icon_path()
        if icon_path is not None:
            self.setWindowIcon(QIcon(str(icon_path)))

        self.settings_path = runtime_base_dir() / "settings.json"
        self.settings = self._load_settings()

        self.ui_queue: queue.Queue[dict] = queue.Queue()
        self.is_busy = False
        self.cancel_requested = False
        self.job_queue: list[DownloadJob] = []
        self.job_items: dict[str, QListWidgetItem] = {}

        self.fps_by_height: dict[int, list[int]] = {}
        self.all_fps: list[int] = []
        self.video_extensions: list[str] = []
        self.current_title = "-"
        self.last_analyzed_url = ""
        self.last_analyzed_formats: list[dict] = []

        self.progress_window: DownloadProgressWindow | None = None

        self.auto_fetch_timer = QTimer(self)
        self.auto_fetch_timer.setSingleShot(True)
        self.auto_fetch_timer.setInterval(800)
        self.auto_fetch_timer.timeout.connect(self._auto_fetch_if_needed)

        self._build_ui()
        self._apply_styles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_ui_queue)
        self.timer.start(100)

    def _build_ui(self) -> None:
        """Build the user interface."""
        root = QWidget()
        self.setCentralWidget(root)

        wrapper = QVBoxLayout(root)
        wrapper.setContentsMargins(20, 20, 20, 20)
        wrapper.setSpacing(12)

        title = QLabel("Social Media Video Downloader")
        title.setObjectName("AppTitle")
        wrapper.addWidget(title)

        top_group = QGroupBox("Source")
        top_layout = QGridLayout(top_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste URL (YouTube, X, Instagram, TikTok, Facebook, etc.)")
        self.url_input.textChanged.connect(self._on_url_text_changed)
        self.fetch_btn = QPushButton("Analyze URL")
        self.fetch_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.fetch_btn.clicked.connect(lambda: self.on_fetch_formats(show_warning=True))
        top_layout.addWidget(QLabel("URL"), 0, 0)
        top_layout.addWidget(self.url_input, 0, 1)
        top_layout.addWidget(self.fetch_btn, 0, 2)

        self.title_value = QLabel("-")
        self.title_value.setObjectName("VideoTitle")
        top_layout.addWidget(QLabel("Title"), 1, 0)
        top_layout.addWidget(self.title_value, 1, 1, 1, 3)
        wrapper.addWidget(top_group)

        options_group = QGroupBox("Download Options")
        options_layout = QGridLayout(options_group)

        self.video_radio = QRadioButton("Video")
        self.audio_radio = QRadioButton("Audio")
        self.video_radio.setChecked(True)
        self.video_radio.toggled.connect(self._on_mode_change)
        mode_row = QHBoxLayout()
        mode_row.addWidget(self.video_radio)
        mode_row.addWidget(self.audio_radio)
        mode_row.addStretch(1)
        options_layout.addWidget(QLabel("Mode"), 0, 0)
        options_layout.addLayout(mode_row, 0, 1, 1, 2)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["best", "1080p", "720p", "480p", "360p"])
        self.quality_combo.currentIndexChanged.connect(self._refresh_fps_values)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["auto"])
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems(["best", "mp4", "webm", "mkv"])
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["mp3", "m4a", "aac", "wav", "flac", "opus"])

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.addRow("Resolution", self.quality_combo)
        form.addRow("FPS", self.fps_combo)
        form.addRow("Video format", self.video_format_combo)
        form.addRow("Audio format", self.audio_format_combo)
        options_layout.addLayout(form, 1, 0, 1, 3)

        self.folder_input = QLineEdit(str(self.settings.get("default_download_dir", default_download_dir())))
        self.browse_btn = QPushButton("Browse Folder")
        self.browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.browse_btn.clicked.connect(self.on_browse_folder)
        options_layout.addWidget(QLabel("Save to"), 2, 0)
        options_layout.addWidget(self.folder_input, 2, 1)
        options_layout.addWidget(self.browse_btn, 2, 2)

        wrapper.addWidget(options_group)

        queue_group = QGroupBox("Queue")
        queue_layout = QVBoxLayout(queue_group)
        self.queue_list = QListWidget()
        queue_layout.addWidget(self.queue_list)

        queue_buttons = QHBoxLayout()
        self.add_queue_btn = QPushButton("Add To Queue")
        self.add_queue_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self.remove_queue_btn = QPushButton("Remove From Queue")
        self.remove_queue_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.start_queue_btn = QPushButton("Start Queue")
        self.start_queue_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.cancel_btn = QPushButton("Cancel Current")
        self.cancel_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.clear_done_btn = QPushButton("Clear Done/Error")
        self.clear_done_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogResetButton))
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self.add_queue_btn.clicked.connect(self.on_add_to_queue)
        self.remove_queue_btn.clicked.connect(self.on_remove_selected_queue)
        self.start_queue_btn.clicked.connect(self._process_next_job)
        self.cancel_btn.clicked.connect(self.on_cancel_current)
        self.clear_done_btn.clicked.connect(self.on_clear_finished)
        self.settings_btn.clicked.connect(self.on_open_settings)
        queue_buttons.addWidget(self.add_queue_btn)
        queue_buttons.addWidget(self.remove_queue_btn)
        queue_buttons.addWidget(self.start_queue_btn)
        queue_buttons.addWidget(self.cancel_btn)
        queue_buttons.addWidget(self.clear_done_btn)
        queue_buttons.addWidget(self.settings_btn)
        queue_layout.addLayout(queue_buttons)
        wrapper.addWidget(queue_group)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        wrapper.addWidget(self.progress)

        self.status_label = QLabel("Ready.")
        wrapper.addWidget(self.status_label)

        self._on_mode_change()

    def _apply_styles(self) -> None:
        """Apply custom stylesheet to the application."""
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #0f172a; color: #e2e8f0; font-size: 13px; }
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 10px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: 600;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #93c5fd; }
            QLabel#AppTitle { font-size: 22px; font-weight: 700; color: #f8fafc; }
            QLabel#VideoTitle { color: #93c5fd; font-weight: 600; }
            QLineEdit, QComboBox, QListWidget {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                color: #f8fafc;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:disabled { background: #475569; color: #cbd5e1; }
            QProgressBar {
                border: 1px solid #334155;
                border-radius: 8px;
                text-align: center;
                background: #1e293b;
            }
            QProgressBar::chunk { background: #22c55e; border-radius: 8px; }
            """
        )

    def on_browse_folder(self) -> None:
        """Handle browse folder button click."""
        current = self.folder_input.text().strip() or str(Path.home() / "Downloads")
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", current)
        if folder:
            self.folder_input.setText(folder)

    def on_fetch_formats(self, show_warning: bool = True) -> None:
        """Fetch available formats for the given URL."""
        if self.is_busy:
            return
        url = self.url_input.text().strip()
        if not url:
            if show_warning:
                QMessageBox.warning(self, "Missing URL", "Please paste a valid social media/video URL first.")
            return
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            self.status_label.setText("⚠ Invalid URL. Please paste a full http/https link.")
            return
        self._set_busy(True)
        self.status_label.setText("Analyzing URL...")
        threading.Thread(target=self._fetch_formats_worker, args=(url,), daemon=True).start()

    def on_add_to_queue(self) -> None:
        """Add a download job to the queue."""
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please paste a valid social media/video URL.")
            return
        if not folder:
            QMessageBox.warning(self, "Missing folder", "Please choose a download folder.")
            return
        try:
            Path(folder).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.critical(self, "Folder Error", f"Cannot use download folder:\n{exc}")
            return

        if any(j.url == url and j.status == "queued" for j in self.job_queue):
            self.status_label.setText("⚠ This URL is already in the queue.")
            return

        estimated_size = self._estimate_file_size(
            self.video_radio.isChecked(),
            self.quality_combo.currentText(),
            self.fps_combo.currentText(),
            self.video_format_combo.currentText(),
            self.audio_format_combo.currentText(),
        )

        job = DownloadJob(
            job_id=uuid4().hex,
            url=url,
            title=self.current_title if self.current_title != "-" else "Unknown title",
            folder=folder,
            video_mode=self.video_radio.isChecked(),
            quality=self.quality_combo.currentText(),
            fps=self.fps_combo.currentText(),
            video_ext=self.video_format_combo.currentText(),
            audio_ext=self.audio_format_combo.currentText(),
            download_playlist=bool(self.settings.get("default_download_playlist", False)),
            retries=int(self.settings.get("max_retries", 2)),
            estimated_size=estimated_size,
        )
        self.job_queue.append(job)
        item = QListWidgetItem(self._queue_item_text(job))
        item.setData(Qt.UserRole, job.job_id)
        self.queue_list.addItem(item)
        self.job_items[job.job_id] = item

        size_msg = f" | Est. size: {human_bytes(estimated_size)}" if estimated_size > 0 else ""
        self.status_label.setText(f"Added to queue.{size_msg}")

        if bool(self.settings.get("auto_start_queue", True)) and not self.is_busy:
            self._process_next_job()

    def on_cancel_current(self) -> None:
        """Cancel the current download."""
        if not self.is_busy:
            self.status_label.setText("No active download to cancel.")
            return
        self.cancel_requested = True
        self.status_label.setText("Cancelling current job...")

    def on_remove_selected_queue(self) -> None:
        """Remove selected items from the queue."""
        selected_items = self.queue_list.selectedItems()
        if not selected_items:
            self.status_label.setText("Select a queue item to remove.")
            return

        remove_ids: set[str] = set()
        blocked_count = 0
        for item in selected_items:
            job_id = self._job_id_from_item(item)
            job = self._find_job(job_id)
            if job is None:
                continue
            if job.status == "downloading":
                blocked_count += 1
                continue
            remove_ids.add(job.job_id)

        if remove_ids:
            self.job_queue = [job for job in self.job_queue if job.job_id not in remove_ids]
            for i in range(self.queue_list.count() - 1, -1, -1):
                item = self.queue_list.item(i)
                if self._job_id_from_item(item) in remove_ids:
                    self.queue_list.takeItem(i)
            for job_id in remove_ids:
                self.job_items.pop(job_id, None)

        if remove_ids and blocked_count:
            self.status_label.setText(f"Removed {len(remove_ids)} item(s). Active download item(s) were kept.")
        elif remove_ids:
            self.status_label.setText(f"Removed {len(remove_ids)} item(s) from queue.")
        elif blocked_count:
            self.status_label.setText("Cannot remove an active downloading item.")
        else:
            self.status_label.setText("No matching queue item found to remove.")

    def on_clear_finished(self) -> None:
        """Clear finished/error items from the queue."""
        kept: list[DownloadJob] = []
        self.queue_list.clear()
        self.job_items.clear()
        for job in self.job_queue:
            if job.status in {"done", "error", "cancelled"}:
                continue
            kept.append(job)
            item = QListWidgetItem(self._queue_item_text(job))
            item.setData(Qt.UserRole, job.job_id)
            self.queue_list.addItem(item)
            self.job_items[job.job_id] = item
        self.job_queue = kept

    def on_open_settings(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() != QDialog.Accepted:
            return
        self.settings.update(dialog.get_settings())
        if not self.folder_input.text().strip():
            self.folder_input.setText(str(self.settings.get("default_download_dir", default_download_dir())))
        self._save_settings()
        self.status_label.setText("Settings saved.")

    # Private methods - Download worker methods

    def _fetch_formats_worker(self, url: str) -> None:
        """Worker thread to fetch available formats."""
        try:
            opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "logger": _SilentYDLLogger()}
            apply_cookie_settings(opts, self.settings)
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as exc:
                if has_cookie_opts(opts) and is_cookie_copy_error(exc):
                    strip_cookie_settings(opts)
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                    self.ui_queue.put(
                        {
                            "type": "status",
                            "message": "Browser cookies unavailable (locked/encrypted). Analyze retried without cookies.",
                        }
                    )
                elif is_youtube_bot_check_error(exc):
                    apply_youtube_client_fallback(opts)
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                    self.ui_queue.put(
                        {
                            "type": "status",
                            "message": "YouTube bot-check detected. Analyze retried with alternate client.",
                        }
                    )
                else:
                    raise

            formats = info.get("formats", [])
            heights = sorted({int(f["height"]) for f in formats if f.get("vcodec") not in (None, "none") and f.get("height")}, reverse=True)
            video_exts = sorted({str(f.get("ext")).lower() for f in formats if f.get("vcodec") not in (None, "none") and f.get("ext")})

            fps_map: dict[int, set[int]] = {}
            all_fps: set[int] = set()
            for fmt in formats:
                if fmt.get("vcodec") in (None, "none"):
                    continue
                h, f = fmt.get("height"), fmt.get("fps")
                if not h or not f:
                    continue
                try:
                    hh = int(h)
                    ff = int(round(float(f)))
                except (TypeError, ValueError):
                    continue
                fps_map.setdefault(hh, set()).add(ff)
                all_fps.add(ff)

            self.ui_queue.put(
                {
                    "type": "formats_ready",
                    "url": url,
                    "title": info.get("title") or "-",
                    "heights": heights,
                    "fps_map": {k: sorted(v) for k, v in fps_map.items()},
                    "all_fps": sorted(all_fps),
                    "video_exts": video_exts,
                    "formats": formats,
                }
            )
        except Exception as exc:
            self.ui_queue.put(
                {
                    "type": "error",
                    "message": (
                        "Format lookup failed.\n"
                        "Tip: for private/restricted posts, open the link in a browser first or use a public URL.\n\n"
                        f"Detail:\n{exc}"
                    ),
                }
            )
        finally:
            self.ui_queue.put({"type": "idle"})

    def _process_next_job(self) -> None:
        """Process the next job in the queue."""
        if self.is_busy:
            return
        pending = next((j for j in self.job_queue if j.status in {"queued", "retry_pending"}), None)
        if pending is None:
            self.status_label.setText("Queue is empty.")
            return

        ffmpeg_location = detect_ffmpeg_location()
        if ffmpeg_location is None:
            QMessageBox.critical(
                self,
                "ffmpeg Not Found",
                "ffmpeg is required for merge/conversion.\nPut ffmpeg in ./ffmpeg/bin or set FFMPEG_DIR in .env.",
            )
            return

        self.cancel_requested = False
        pending.status = "downloading"
        pending.attempt += 1
        self._update_job_item(pending)
        self.progress.setValue(0)
        self.status_label.setText(f"Downloading: {pending.title}")
        self._set_busy(True)

        self.progress_window = DownloadProgressWindow(
            parent=self,
            job=pending,
            on_cancel_callback=self.on_cancel_current,
        )
        self.progress_window.show()

        threading.Thread(target=self._download_worker, args=(pending, ffmpeg_location), daemon=True).start()

    def _download_worker(self, job: DownloadJob, ffmpeg_location: str) -> None:
        """Worker thread to download video/audio."""
        base_opts = {
            "noplaylist": not job.download_playlist,
            "outtmpl": str(Path(job.folder) / "%(title).200B [%(id)s].%(ext)s"),
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
            "ffmpeg_location": ffmpeg_location,
            "logger": _SilentYDLLogger(),
        }
        apply_cookie_settings(base_opts, self.settings)

        try:
            errors: list[str] = []
            max_attempts = max(1, int(job.retries) + 1)
            for attempt in range(1, max_attempts + 1):
                if self.cancel_requested:
                    raise DownloadError("Cancelled by user.")

                job.attempt = attempt
                self.ui_queue.put({"type": "job_status", "job_id": job.job_id, "status": "retrying" if attempt > 1 else "downloading"})
                self.ui_queue.put({"type": "status", "message": f"Downloading attempt {attempt}/{max_attempts}..."})

                try:
                    primary = dict(base_opts)
                    if job.video_mode:
                        primary["format"] = self._build_video_format_selector(job.quality, job.fps, job.video_ext)
                        primary["merge_output_format"] = job.video_ext if job.video_ext != "best" else "mp4"
                    else:
                        primary["format"] = "bestaudio/best"
                        primary["postprocessors"] = [
                            {"key": "FFmpegExtractAudio", "preferredcodec": job.audio_ext, "preferredquality": "192"}
                        ]

                    with yt_dlp.YoutubeDL(primary) as ydl:
                        ydl.download([job.url])
                    self.ui_queue.put({"type": "job_done", "job_id": job.job_id, "message": f"Finished. Saved to:\n{job.folder}"})
                    return
                except Exception as exc:
                    if self.cancel_requested:
                        raise DownloadError("Cancelled by user.")
                    if has_cookie_opts(base_opts) and is_cookie_copy_error(exc):
                        strip_cookie_settings(base_opts)
                        errors.append(f"Cookies disabled after browser lock: {exc}")
                        continue
                    if is_youtube_bot_check_error(exc):
                        try:
                            alt = dict(primary)
                            apply_youtube_client_fallback(alt)
                            with yt_dlp.YoutubeDL(alt) as ydl:
                                ydl.download([job.url])
                            self.ui_queue.put(
                                {
                                    "type": "job_done",
                                    "job_id": job.job_id,
                                    "message": f"Finished (youtube client fallback). Saved to:\n{job.folder}",
                                }
                            )
                            return
                        except Exception as fallback_client_exc:
                            errors.append(f"YouTube client fallback: {fallback_client_exc}")
                    errors.append(str(exc))

                    try:
                        fallback = dict(base_opts)
                        if job.video_mode:
                            fallback["format"] = "bv*+ba/best"
                            fallback["merge_output_format"] = "mp4"
                        else:
                            fallback["format"] = "bestaudio/best"
                            fallback["postprocessors"] = [
                                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
                            ]
                        with yt_dlp.YoutubeDL(fallback) as ydl:
                            ydl.download([job.url])
                        self.ui_queue.put({"type": "job_done", "job_id": job.job_id, "message": f"Finished (fallback). Saved to:\n{job.folder}"})
                        return
                    except Exception as fallback_exc:
                        errors.append(f"Fallback: {fallback_exc}")

            raise DownloadError(" | ".join(errors[-3:]))

        except Exception as exc:
            if self.cancel_requested:
                self.ui_queue.put({"type": "job_cancelled", "job_id": job.job_id, "message": "Download cancelled by user."})
            else:
                self.ui_queue.put({"type": "job_error", "job_id": job.job_id, "message": f"Download failed:\n{exc}"})
        finally:
            self.ui_queue.put({"type": "job_idle"})

    def _build_video_format_selector(self, quality: str, fps_label: str, video_ext: str) -> str:
        """Build yt-dlp format selector string."""
        height_filter = ""
        fps_filter = ""
        ext_filter = f"[ext={video_ext}]" if video_ext and video_ext != "best" else ""

        if quality != "best":
            try:
                height_filter = f"[height<=?{int(quality.rstrip('p'))}]"
            except ValueError:
                pass

        if fps_label != "auto":
            try:
                fps_filter = f"[fps<=?{int(fps_label.split()[0])}]"
            except ValueError:
                pass

        return (
            f"bv*{ext_filter}{height_filter}{fps_filter}+ba/"
            f"b{ext_filter}{height_filter}{fps_filter}/"
            f"bv*{height_filter}{fps_filter}+ba/"
            f"b{height_filter}{fps_filter}"
        )

    def _progress_hook(self, data: dict) -> None:
        """Handle download progress updates."""
        if self.cancel_requested:
            raise DownloadError("Cancelled by user.")

        status = data.get("status")
        if status == "downloading":
            downloaded = data.get("downloaded_bytes", 0) or 0
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            percent = (downloaded / total * 100.0) if total else 0.0

            speed = data.get("speed")
            eta = data.get("eta")
            message = f"Downloading... {percent:.1f}%"
            if speed:
                message += f" | {human_bytes(speed)}/s"
            if eta is not None:
                message += f" | ETA {int(eta)}s"
            self.ui_queue.put({"type": "progress", "percent": percent, "message": message, "downloaded_bytes": downloaded, "total_bytes": total})
        elif status == "finished":
            self.ui_queue.put({"type": "progress", "percent": 100.0, "message": "Download complete. Processing with ffmpeg...", "downloaded_bytes": 0, "total_bytes": 0})

    def _poll_ui_queue(self) -> None:
        """Poll the UI queue for messages from worker threads."""
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                t = msg.get("type")

                if t == "progress":
                    percent = float(msg.get("percent", 0.0))
                    self.progress.setValue(int(percent))
                    self.status_label.setText(msg.get("message", "Working..."))
                    if self.progress_window is not None:
                        self.progress_window.update_progress(
                            percent,
                            msg.get("message", "Working..."),
                            int(msg.get("downloaded_bytes", 0)),
                            int(msg.get("total_bytes", 0)),
                        )

                elif t == "status":
                    self.status_label.setText(msg.get("message", "Working..."))

                elif t == "formats_ready":
                    self.last_analyzed_url = msg.get("url", "").strip()
                    self.current_title = msg.get("title", "-")
                    self.title_value.setText(self.current_title)
                    self.last_analyzed_formats = msg.get("formats", [])

                    self.fps_by_height = msg.get("fps_map", {})
                    self.all_fps = msg.get("all_fps", [])
                    heights = msg.get("heights", [])
                    qualities = ["best"] + [f"{h}p" for h in heights]
                    if len(qualities) == 1:
                        qualities += ["1080p", "720p", "480p", "360p"]
                    self.quality_combo.clear()
                    self.quality_combo.addItems(qualities)

                    self.video_extensions = msg.get("video_exts", [])
                    exts = ["best"] + [x for x in self.video_extensions if x not in {"best"}]
                    if not exts:
                        exts = ["best", "mp4", "webm", "mkv"]
                    self.video_format_combo.clear()
                    self.video_format_combo.addItems(exts)

                    self._refresh_fps_values()
                    self.status_label.setText("Formats loaded.")

                elif t == "job_status":
                    job = self._find_job(msg.get("job_id"))
                    if job is not None:
                        job.status = str(msg.get("status", job.status))
                        self._update_job_item(job)

                elif t == "job_done":
                    job = self._find_job(msg.get("job_id"))
                    if job is not None:
                        job.status = "done"
                        self._update_job_item(job)
                    self.progress.setValue(100)
                    self.status_label.setText("Finished.")
                    show_popup = bool(self.settings.get("show_success_popup", True))
                    if self.progress_window is not None:
                        if show_popup:
                            self.progress_window.close()
                        else:
                            self.progress_window.mark_done()
                            QTimer.singleShot(1600, lambda: setattr(self, "progress_window", None))
                        self.progress_window = None
                    if show_popup:
                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Download Complete")
                        msg_box.setText(msg.get("message", "Done."))
                        open_folder_btn = msg_box.addButton("Open Folder", QMessageBox.ActionRole)
                        msg_box.addButton(QMessageBox.Ok)
                        msg_box.exec()
                        if msg_box.clickedButton() == open_folder_btn and job is not None:
                            if sys.platform == "win32":
                                subprocess.Popen(["explorer", job.folder])
                            else:
                                subprocess.Popen(["xdg-open", job.folder])

                elif t == "job_error":
                    job = self._find_job(msg.get("job_id"))
                    if job is not None:
                        job.status = "error"
                        self._update_job_item(job)
                    self.status_label.setText("Error.")
                    if self.progress_window is not None:
                        self.progress_window.mark_error(msg.get("message", "Something went wrong."))
                    else:
                        QMessageBox.critical(self, "Error", msg.get("message", "Something went wrong."))

                elif t == "job_cancelled":
                    job = self._find_job(msg.get("job_id"))
                    if job is not None:
                        job.status = "cancelled"
                        self._update_job_item(job)
                    self.status_label.setText(msg.get("message", "Cancelled."))
                    if self.progress_window is not None:
                        self.progress_window.mark_cancelled()
                        QTimer.singleShot(1100, lambda: setattr(self, "progress_window", None))

                elif t == "job_idle":
                    self.cancel_requested = False
                    self._set_busy(False)
                    self._process_next_job()

                elif t == "error":
                    self.status_label.setText("Error.")
                    QMessageBox.critical(self, "Error", msg.get("message", "Something went wrong."))

                elif t == "idle":
                    self._set_busy(False)
        except queue.Empty:
            pass

    def _refresh_fps_values(self) -> None:
        """Refresh FPS combo box values based on quality."""
        quality = self.quality_combo.currentText()
        if quality == "best":
            fps_values = self.all_fps
        else:
            try:
                fps_values = self.fps_by_height.get(int(quality.rstrip("p")), [])
            except ValueError:
                fps_values = []

        values = ["auto"] + [f"{x} fps" for x in fps_values]
        cur = self.fps_combo.currentText()
        self.fps_combo.clear()
        self.fps_combo.addItems(values)
        idx = self.fps_combo.findText(cur)
        self.fps_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _on_mode_change(self) -> None:
        """Handle mode (video/audio) change."""
        video_mode = self.video_radio.isChecked()
        self.quality_combo.setEnabled(video_mode)
        self.fps_combo.setEnabled(video_mode)
        self.video_format_combo.setEnabled(video_mode)
        self.audio_format_combo.setEnabled(not video_mode)

    def _set_busy(self, busy: bool) -> None:
        """Set busy state and disable/enable controls accordingly."""
        self.is_busy = busy
        self.fetch_btn.setEnabled(not busy)
        self.start_queue_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(busy)
        if not busy and self.status_label.text().lower() not in {"finished.", "error.", "ready."}:
            self.status_label.setText("Ready.")

    def _on_url_text_changed(self, text: str) -> None:
        """Handle URL text change."""
        cleaned = text.strip()
        if cleaned != self.last_analyzed_url:
            self.title_value.setText("-")
            self.current_title = "-"

        if not bool(self.settings.get("auto_analyze", False)) or self.is_busy:
            return
        if len(cleaned) < 8:
            self.auto_fetch_timer.stop()
            return
        self.auto_fetch_timer.start()

    def _auto_fetch_if_needed(self) -> None:
        """Auto-fetch formats if timer fires."""
        url = self.url_input.text().strip()
        if self.is_busy or len(url) < 8 or url == self.last_analyzed_url:
            return
        self.on_fetch_formats(show_warning=False)

    def _estimate_file_size(self, video_mode: bool, quality: str, fps_label: str, video_ext: str, audio_ext: str) -> int:
        """Estimate file size based on selected format options."""
        if not self.last_analyzed_formats:
            return 0

        total_size = 0

        if video_mode:
            height_filter = 0
            if quality != "best":
                try:
                    height_filter = int(quality.rstrip('p'))
                except ValueError:
                    height_filter = 0

            fps_filter_val = 0
            if fps_label != "auto":
                try:
                    fps_filter_val = int(fps_label.split()[0])
                except ValueError:
                    fps_filter_val = 0

            best_video_format = None
            best_audio_format = None

            for fmt in self.last_analyzed_formats:
                if fmt.get("vcodec") not in (None, "none"):
                    fmt_height = fmt.get("height", 0)
                    fmt_fps = fmt.get("fps", 0)
                    fmt_ext = str(fmt.get("ext", "")).lower()

                    height_ok = height_filter == 0 or fmt_height <= height_filter
                    fps_ok = fps_filter_val == 0 or fmt_fps <= fps_filter_val
                    ext_ok = video_ext == "best" or fmt_ext == video_ext

                    if height_ok and fps_ok:
                        if best_video_format is None or (fmt_height, fmt_fps) > (best_video_format.get("height", 0), best_video_format.get("fps", 0)):
                            if ext_ok or video_ext == "best":
                                best_video_format = fmt

                elif fmt.get("acodec") not in (None, "none"):
                    if best_audio_format is None or fmt.get("abr", 0) > best_audio_format.get("abr", 0):
                        best_audio_format = fmt

            if best_video_format:
                total_size += best_video_format.get("filesize", 0) or best_video_format.get("filesize_approx", 0) or 0
            if best_audio_format:
                total_size += best_audio_format.get("filesize", 0) or best_audio_format.get("filesize_approx", 0) or 0
        else:
            best_audio = None
            for fmt in self.last_analyzed_formats:
                if fmt.get("acodec") not in (None, "none"):
                    if best_audio is None or fmt.get("abr", 0) > best_audio.get("abr", 0):
                        best_audio = fmt

            if best_audio:
                total_size = best_audio.get("filesize", 0) or best_audio.get("filesize_approx", 0) or 0

        return int(total_size)

    def _queue_item_text(self, job: DownloadJob) -> str:
        """Generate display text for a queue item."""
        mode = "VIDEO" if job.video_mode else "AUDIO"
        size_str = f" | {human_bytes(job.estimated_size)}" if job.estimated_size > 0 else ""
        return f"[{job.status.upper()}] {mode} | {job.title}{size_str} | {job.url}"

    def _update_job_item(self, job: DownloadJob) -> None:
        """Update display of a queue item."""
        item = self.job_items.get(job.job_id)
        if item is not None:
            item.setText(self._queue_item_text(job))

    def _find_job(self, job_id: str | None) -> DownloadJob | None:
        """Find a download job by ID."""
        if not job_id:
            return None
        for job in self.job_queue:
            if job.job_id == job_id:
                return job
        return None

    def _job_id_from_item(self, item: QListWidgetItem | None) -> str | None:
        """Get job ID from a queue list item."""
        if item is None:
            return None
        job_id = item.data(Qt.UserRole)
        if isinstance(job_id, str) and job_id:
            return job_id
        for candidate_id, candidate_item in self.job_items.items():
            if candidate_item is item:
                return candidate_id
        return None

    def _load_settings(self) -> dict:
        """Load settings from JSON file."""
        defaults = {
            "default_download_dir": default_download_dir(),
            "show_success_popup": True,
            "auto_analyze": False,
            "auto_start_queue": True,
            "default_download_playlist": False,
            "cookies_from_browser": "none",
            "cookies_file": "",
            "max_retries": 2,
        }
        if not self.settings_path.exists():
            return defaults
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update(data)
        except Exception as e:
            logger.exception("Failed to load settings: %s", e)
        return defaults

    def _save_settings(self) -> None:
        """Save settings to JSON file."""
        self.settings["default_download_dir"] = self.folder_input.text().strip() or default_download_dir()
        try:
            self.settings_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except Exception as e:
            logger.exception("Failed to save settings: %s", e)
            self.status_label.setText("Warning: Failed to save settings.")
