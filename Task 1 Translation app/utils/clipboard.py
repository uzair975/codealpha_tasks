"""
Translator Pro — Clipboard integration utility.
"""
from PySide6.QtWidgets import QApplication


def copy_to_clipboard(text: str) -> bool:
    """
    Copy *text* to the OS clipboard via Qt.

    Returns True on success, False if QApplication is not available.
    """
    app = QApplication.instance()
    if app is None:
        return False
    clipboard = app.clipboard()
    clipboard.setText(text)
    return True
