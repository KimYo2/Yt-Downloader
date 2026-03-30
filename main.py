"""
YtDownloader - Social Media Video Downloader
Main entry point for the application.
"""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from utils import load_env, find_app_icon_path
from windows import DownloaderWindow


def main() -> None:
    """Main entry point."""
    load_env()
    app = QApplication(sys.argv)
    icon_path = find_app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    window = DownloaderWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
