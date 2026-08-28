"""
Translator Pro — Debounce helper for auto-translate-on-typing.

Usage::

    debouncer = DebounceTimer(delay_ms=500)
    debouncer.timeout.connect(do_translate)

    # In the text-changed handler:
    debouncer.trigger()          # resets the countdown every keystroke
"""
from PySide6.QtCore import QTimer, Signal, QObject


class DebounceTimer(QObject):
    """
    Single-shot timer that restarts on every ``trigger()`` call.
    Emits ``triggered`` only when the user stops typing for *delay_ms*.
    """

    triggered = Signal()

    def __init__(self, delay_ms: int = 500, parent: QObject | None = None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self.triggered.emit)

    def trigger(self) -> None:
        """(Re)start the countdown."""
        self._timer.start()

    def cancel(self) -> None:
        """Cancel any pending fire."""
        self._timer.stop()

    @property
    def is_active(self) -> bool:
        return self._timer.isActive()
