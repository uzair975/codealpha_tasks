"""
Translator Pro — Application Entry Point.

Initialises QApplication, loads the dark theme, creates the main window,
and enters the Qt event loop.
"""
import sys
import os
import logging

# Suppress Qt system font database warnings on Windows
os.environ["QT_LOGGING_RULES"] = "qt.text.font.db.warning=false"

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from config.settings import STYLES_DIR, WINDOW_TITLE
from ui.main_window import MainWindow


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_stylesheet(app: QApplication) -> None:
    """Apply the dark theme QSS to the entire application."""
    qss_path = STYLES_DIR / "dark_theme.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as fh:
            app.setStyleSheet(fh.read())


def main() -> None:
    _configure_logging()

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)
    app.setApplicationDisplayName(WINDOW_TITLE)

    # Set default font (Inter if available, else Segoe UI)
    font = QFont("Inter", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    _load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
