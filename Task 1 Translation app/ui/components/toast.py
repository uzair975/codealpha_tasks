"""
Translator Pro — Floating toast notification widget.

Slides in from the top-center of its parent, auto-hides after a timeout.
Supports ``info``, ``success``, and ``error`` severity levels.
"""
from __future__ import annotations

from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QPoint,
    QTimer,
    Qt,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

import qtawesome as qta

from config.settings import TOAST_DURATION_MS


# Severity → (icon name, icon color, QSS object-name suffix)
_SEVERITY_MAP = {
    "info":    ("fa5s.info-circle",       "#6366F1", "toastInfo"),
    "success": ("fa5s.check-circle",      "#22C55E", "toastSuccess"),
    "error":   ("fa5s.exclamation-circle", "#EF4444", "toastError"),
}


class Toast(QFrame):
    """
    Non-modal, auto-dismissing notification overlay.

    Usage::

        Toast.show_message(parent, "Copied!", severity="success")
    """

    _active_toasts: list[Toast] = []  # track so we can stack them

    def __init__(
        self,
        message: str,
        severity: str = "info",
        duration_ms: int = TOAST_DURATION_MS,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        icon_name, icon_color, obj_name = _SEVERITY_MAP.get(
            severity, _SEVERITY_MAP["info"]
        )

        self.setObjectName(obj_name)

        # ── Layout ─────────────────────────────────────────────────────
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(
            qta.icon(icon_name, color=icon_color).pixmap(18, 18)
        )
        layout.addWidget(icon_label)

        text_label = QLabel(message)
        text_label.setStyleSheet("font-size: 13px; font-weight: 500;")
        layout.addWidget(text_label)

        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

        # ── Auto-dismiss timer ─────────────────────────────────────────
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.setInterval(duration_ms)
        self._dismiss_timer.timeout.connect(self._slide_out)

    # ── class method (convenience) ──────────────────────────────────────

    @classmethod
    def show_message(
        cls,
        parent: QWidget,
        message: str,
        severity: str = "info",
        duration_ms: int = TOAST_DURATION_MS,
    ) -> Toast:
        """Create and display a toast anchored to *parent*."""
        toast = cls(message, severity, duration_ms, parent)
        toast._show_animated()
        cls._active_toasts.append(toast)
        return toast

    # ── animation ───────────────────────────────────────────────────────

    def _show_animated(self) -> None:
        """Position above the parent's top-center and slide down."""
        parent = self.parentWidget()
        if parent is None:
            self.show()
            return

        pw = parent.width()
        tw = self.sizeHint().width()
        x = (pw - tw) // 2

        # Stack below any existing toasts
        y_offset = 12
        for t in Toast._active_toasts:
            if t.isVisible() and t.parentWidget() is parent:
                y_offset += t.height() + 8

        start = QPoint(x, -self.height())
        end = QPoint(x, y_offset)

        self.move(start)
        self.show()

        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(300)
        self._slide_anim.setStartValue(start)
        self._slide_anim.setEndValue(end)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.start()

        self._dismiss_timer.start()

    def _slide_out(self) -> None:
        """Slide up and destroy."""
        start = self.pos()
        end = QPoint(start.x(), -self.height())

        self._out_anim = QPropertyAnimation(self, b"pos")
        self._out_anim.setDuration(250)
        self._out_anim.setStartValue(start)
        self._out_anim.setEndValue(end)
        self._out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._out_anim.finished.connect(self._cleanup)
        self._out_anim.start()

    def _cleanup(self) -> None:
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
        self.close()
        self.deleteLater()
