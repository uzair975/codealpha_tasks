"""
Translator Pro — Text pane component with action toolbar and animated hover effects.

Each pane contains:
- A QPlainTextEdit with animated color transitions.
- A bottom toolbar strip with Copy, Listen (TTS / Volume), Clear buttons with smooth hover animations.
- A word/character counter badge (bottom-right).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import qtawesome as qta
from ui.components.anim_effects import AnimatedTextBox, AnimatedIconButton


class TextPane(QWidget):
    """
    Custom text area panel with an integrated action toolbar.

    Parameters
    ----------
    placeholder : str
        Placeholder text shown when the editor is empty.
    read_only : bool
        If True, the text area is not editable (used for the target pane).

    Signals
    -------
    text_changed(str)
        Emitted every time the user types (full text content).
    copy_requested()
        Emitted when the Copy button is clicked.
    listen_requested()
        Emitted when the Speaker button is clicked.
    clear_requested()
        Emitted when the Clear button is clicked.
    """

    text_changed = Signal(str)
    copy_requested = Signal()
    listen_requested = Signal()
    clear_requested = Signal()

    def __init__(
        self,
        placeholder: str = "Type or paste text here…",
        read_only: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._read_only = read_only
        self._build_ui(placeholder)

    # ── public API ──────────────────────────────────────────────────────

    def get_text(self) -> str:
        return self._editor.toPlainText()

    def set_text(self, text: str) -> None:
        self._editor.setPlainText(text)

    def clear(self) -> None:
        self._editor.clear()

    def set_read_only(self, flag: bool) -> None:
        self._editor.setReadOnly(flag)
        self._read_only = flag

    # ── build ───────────────────────────────────────────────────────────

    def _build_ui(self, placeholder: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── Text editor ────────────────────────────────────────────────
        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText(placeholder)
        self._editor.setReadOnly(self._read_only)
        self._editor.setTabChangesFocus(True)

        # Ensure high-contrast solid typography
        editor_font = self._editor.font()
        editor_font.setFamily("Segoe UI")
        editor_font.setPointSize(11)
        editor_font.setWeight(QFont.Weight.Medium)
        self._editor.setFont(editor_font)

        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor, stretch=1)

        # Attach smooth color-changing animation controller to text box
        self._anim_editor = AnimatedTextBox(self._editor)
        self._anim_editor.apply_state(0.0)

        # ── Bottom toolbar ─────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 0, 4, 0)
        toolbar.setSpacing(6)

        self._copy_btn = self._icon_button("fa5s.copy", "Copy to clipboard")
        self._listen_btn = self._icon_button("fa5s.volume-up", "Listen (TTS)")
        self._clear_btn = self._icon_button("fa5s.times", "Clear text")

        self._copy_btn.clicked.connect(self.copy_requested.emit)
        self._listen_btn.clicked.connect(self.listen_requested.emit)
        self._clear_btn.clicked.connect(self._on_clear)

        # Attach smooth color-changing animation controllers to toolbar buttons
        self._anim_copy = AnimatedIconButton(self._copy_btn, "fa5s.copy")
        self._anim_listen = AnimatedIconButton(self._listen_btn, "fa5s.volume-up")
        self._anim_clear = AnimatedIconButton(self._clear_btn, "fa5s.times")

        toolbar.addWidget(self._copy_btn)
        toolbar.addWidget(self._listen_btn)
        toolbar.addWidget(self._clear_btn)
        toolbar.addStretch()

        # ── Counter badge ──────────────────────────────────────────────
        self._counter = QLabel("0 chars · 0 words")
        self._counter.setObjectName("badgeLabel")
        toolbar.addWidget(self._counter)

        layout.addLayout(toolbar)

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _icon_button(icon_name: str, tooltip: str) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("iconBtn")
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(32, 32)
        return btn

    def _on_text_changed(self) -> None:
        text = self._editor.toPlainText()
        # Update counter
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self._counter.setText(f"{chars:,} chars · {words:,} words")
        # Emit signal
        self.text_changed.emit(text)

    def _on_clear(self) -> None:
        self._editor.clear()
        self.clear_requested.emit()
