"""Data models for YtDownloader application."""

from dataclasses import dataclass


@dataclass
class DownloadJob:
    """Represents a download job with all its configuration."""
    job_id: str
    url: str
    title: str
    folder: str
    video_mode: bool
    quality: str
    fps: str
    video_ext: str
    audio_ext: str
    download_playlist: bool
    retries: int
    status: str = "queued"
    attempt: int = 0
    estimated_size: int = 0
