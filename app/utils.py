"""Utility functions and helpers for YtDownloader application."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


class _SilentYDLLogger:
    """Silent logger for yt-dlp to suppress output."""

    def debug(self, _msg: str) -> None:
        return

    def warning(self, _msg: str) -> None:
        return

    def error(self, _msg: str) -> None:
        return


def runtime_base_dir() -> Path:
    """Get the base directory for runtime files."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def load_env() -> None:
    """Load environment variables from .env file."""
    if load_dotenv is None:
        return
    env_path = runtime_base_dir() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)


def find_app_icon_path() -> Path | None:
    """Find application icon path from various locations."""
    names = ("icon.ico", "icon.png")
    roots: list[Path] = [runtime_base_dir()]
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
        roots = [exe_dir, meipass, *roots]

    for root in roots:
        for name in names:
            candidate = root / "icons" / name
            if candidate.exists():
                return candidate
    return None


def human_bytes(num: float) -> str:
    """Convert bytes to human-readable format."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num)
    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def default_download_dir() -> str:
    """Get default download directory from env or system."""
    configured = os.getenv("DEFAULT_DOWNLOAD_DIR", "").strip()
    if configured:
        return str(Path(configured).expanduser())
    return str(Path.home() / "Downloads")


def detect_ffmpeg_location() -> str | None:
    """Detect FFmpeg location from various paths."""
    candidates: list[Path] = []

    env_ffmpeg = os.getenv("FFMPEG_DIR", "").strip()
    if env_ffmpeg:
        env_path = Path(env_ffmpeg).expanduser()
        if env_path.is_file():
            candidates.append(env_path.parent)
        else:
            candidates.extend([env_path, env_path / "bin"])

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
        candidates.extend([exe_dir / "ffmpeg" / "bin", exe_dir / "ffmpeg", meipass / "ffmpeg" / "bin", meipass / "ffmpeg"])
    else:
        base = runtime_base_dir()
        candidates.extend([base / "ffmpeg" / "bin", base / "ffmpeg"])

    for folder in candidates:
        if is_working_ffmpeg_dir(folder):
            return str(folder)

    ffmpeg_on_path = shutil.which("ffmpeg")
    if ffmpeg_on_path:
        path_dir = Path(ffmpeg_on_path).resolve().parent
        if is_working_ffmpeg_dir(path_dir):
            return str(path_dir)
    return None


def is_working_ffmpeg_dir(folder: Path) -> bool:
    """Check if a directory contains working FFmpeg."""
    exe = folder / "ffmpeg.exe"
    if not exe.exists():
        exe = folder / "ffmpeg"
        if not exe.exists():
            return False
    try:
        result = subprocess.run(
            [str(exe), "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=4,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0 and "ffmpeg version" in (result.stdout or "").lower()
    except Exception:
        return False


def is_cookie_copy_error(exc: Exception) -> bool:
    """Check if exception is related to cookie copy error."""
    text = str(exc).lower()
    return (
        "could not copy chrome cookie database" in text
        or "cookie database" in text
        or "failed to decrypt with dpapi" in text
        or "dpapi" in text
        or "failed to decrypt" in text
    )


def is_youtube_bot_check_error(exc: Exception) -> bool:
    """Check if exception is related to YouTube bot check."""
    text = str(exc).lower()
    return "sign in to confirm you're not a bot" in text


def apply_youtube_client_fallback(opts: dict) -> None:
    """Apply YouTube client fallback options."""
    opts["extractor_args"] = {"youtube": {"player_client": ["android", "web_safari"]}}


def apply_cookie_settings(opts: dict, settings: dict) -> None:
    """Apply cookie settings to yt-dlp options."""
    cookies_file = str(settings.get("cookies_file", "")).strip()
    if cookies_file:
        cookie_path = Path(cookies_file).expanduser()
        if cookie_path.exists():
            opts["cookiefile"] = str(cookie_path)
            return

    browser = str(settings.get("cookies_from_browser", "none")).strip().lower()
    if browser and browser != "none":
        opts["cookiesfrombrowser"] = (browser,)


def strip_cookie_settings(opts: dict) -> None:
    """Remove cookie settings from yt-dlp options."""
    opts.pop("cookiefile", None)
    opts.pop("cookiesfrombrowser", None)


def has_cookie_opts(opts: dict) -> bool:
    """Check if yt-dlp options has cookie settings."""
    return "cookiefile" in opts or "cookiesfrombrowser" in opts
