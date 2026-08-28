"""
Translator Pro — Main Application Window with animated hover effects.

Layout
------
┌──────────────────────────────────────────────────────────────────┐
│  [Source Dropdown]  ⇄  [Swap]  ⇄  [Target Dropdown]    [☀/🌙]  │
├───────────────────────────┬──────────────────────────────────────┤
│  Source TextPane           │  Target TextPane (read-only)        │
│  (editable, auto-translate)│                                     │
├───────────────────────────┴──────────────────────────────────────┤
│  [Auto-translate ☑]   [▶ Translate]              Provider badge  │
└──────────────────────────────────────────────────────────────────┘
"""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

import qtawesome as qta

from config.settings import (
    DEFAULT_SOURCE_LANG,
    DEFAULT_TARGET_LANG,
    DEBOUNCE_DELAY_MS,
    STYLES_DIR,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)
from core.interfaces import TranslationResult
from core.tts_engine import TTSManager
from ui.components.lang_selector import LanguageSelector
from ui.components.text_pane import TextPane
from ui.components.toast import Toast
from ui.components.anim_effects import (
    AnimatedTranslateButton,
    AnimatedSwapButton,
    AnimatedIconButton,
    notify_theme_changed,
)
from ui.workers import TranslationWorker
from utils.clipboard import copy_to_clipboard
from utils.debounce import DebounceTimer

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._is_dark = True
        self._thread_pool = QThreadPool.globalInstance()
        self._tts = TTSManager()
        self._debouncer = DebounceTimer(delay_ms=DEBOUNCE_DELAY_MS, parent=self)

        self._build_ui()
        self._connect_signals()
        self._apply_theme()

        # Center on screen
        self._center()

    # ════════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 14)
        root.setSpacing(12)

        # ── Top bar ────────────────────────────────────────────────────
        root.addLayout(self._build_top_bar())

        # ── Editor splitter ────────────────────────────────────────────
        root.addWidget(self._build_editor_area(), stretch=1)

        # ── Bottom toolbar ─────────────────────────────────────────────
        root.addLayout(self._build_bottom_bar())

    # ── Top Bar ────────────────────────────────────────────────────────

    def _build_top_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(12)

        # App icon + title
        title_label = QLabel(f"  {WINDOW_TITLE}")
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: 700; letter-spacing: 0.5px;"
        )
        bar.addWidget(title_label)
        bar.addStretch()

        # Source language selector
        src_label = QLabel("FROM")
        src_label.setObjectName("secondaryLabel")
        bar.addWidget(src_label)

        self._src_selector = LanguageSelector(
            default_code=DEFAULT_SOURCE_LANG, exclude_auto=False
        )
        bar.addWidget(self._src_selector)

        # Swap button with hover animation
        self._swap_btn = QPushButton()
        self._swap_btn.setObjectName("swapBtn")
        self._swap_btn.setToolTip("Swap languages")
        self._swap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim_swap = AnimatedSwapButton(self._swap_btn, is_dark=self._is_dark)
        bar.addWidget(self._swap_btn)

        # Target language selector
        tgt_label = QLabel("TO")
        tgt_label.setObjectName("secondaryLabel")
        bar.addWidget(tgt_label)

        self._tgt_selector = LanguageSelector(
            default_code=DEFAULT_TARGET_LANG, exclude_auto=True
        )
        bar.addWidget(self._tgt_selector)

        bar.addStretch()

        # Theme toggle
        self._theme_btn = QPushButton()
        self._theme_btn.setObjectName("themeToggle")
        self._update_theme_icon()
        self._theme_btn.setToolTip("Toggle light / dark theme")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bar.addWidget(self._theme_btn)

        return bar

    # ── Editor area ────────────────────────────────────────────────────

    def _build_editor_area(self) -> QSplitter:
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(3)

        self._source_pane = TextPane(
            placeholder="Type or paste text to translate…",
            read_only=False,
        )
        self._target_pane = TextPane(
            placeholder="Translation will appear here…",
            read_only=True,
        )

        self._splitter.addWidget(self._source_pane)
        self._splitter.addWidget(self._target_pane)
        self._splitter.setSizes([500, 500])

        return self._splitter

    # ── Bottom bar ─────────────────────────────────────────────────────

    def _build_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(12)

        # Auto-translate checkbox
        self._auto_cb = QCheckBox("Auto-translate")
        self._auto_cb.setChecked(True)
        self._auto_cb.setToolTip(
            "Automatically translate as you type (500 ms debounce)"
        )
        bar.addWidget(self._auto_cb)

        # Layout toggle with hover animation
        self._layout_btn = QPushButton()
        self._layout_btn.setObjectName("iconBtn")
        self._layout_btn.setToolTip("Toggle side-by-side / stacked layout")
        self._layout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._layout_btn.setFixedSize(32, 32)
        self._anim_layout = AnimatedIconButton(self._layout_btn, "fa5s.columns", is_dark=self._is_dark)
        bar.addWidget(self._layout_btn)

        bar.addStretch()

        # Provider badge
        self._provider_label = QLabel("")
        self._provider_label.setObjectName("badgeLabel")
        self._provider_label.setVisible(False)
        bar.addWidget(self._provider_label)

        # Translate button with hover animation
        self._translate_btn = QPushButton("  Translate")
        self._translate_btn.setObjectName("translateBtn")
        self._translate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim_translate = AnimatedTranslateButton(self._translate_btn, is_dark=self._is_dark)
        self._anim_translate.apply_state(0.0)
        bar.addWidget(self._translate_btn)

        return bar

    # ════════════════════════════════════════════════════════════════════
    #  SIGNAL WIRING
    # ════════════════════════════════════════════════════════════════════

    def _connect_signals(self) -> None:
        # Translate button
        self._translate_btn.clicked.connect(self._do_translate)

        # Auto-translate debounce chain
        self._source_pane.text_changed.connect(self._on_source_text_changed)
        self._debouncer.triggered.connect(self._do_translate)

        # Swap
        self._swap_btn.clicked.connect(self._on_swap)

        # Copy
        self._source_pane.copy_requested.connect(
            lambda: self._copy_text(self._source_pane.get_text())
        )
        self._target_pane.copy_requested.connect(
            lambda: self._copy_text(self._target_pane.get_text())
        )

        # Listen (TTS)
        self._source_pane.listen_requested.connect(
            lambda: self._speak(
                self._source_pane.get_text(), self._src_selector.current_code()
            )
        )
        self._target_pane.listen_requested.connect(
            lambda: self._speak(
                self._target_pane.get_text(), self._tgt_selector.current_code()
            )
        )

        # Clear
        self._source_pane.clear_requested.connect(self._target_pane.clear)

        # Theme
        self._theme_btn.clicked.connect(self._toggle_theme)

        # Layout toggle
        self._layout_btn.clicked.connect(self._toggle_layout)

        # TTS signals → UI feedback
        self._tts.signals.started.connect(
            lambda: self._set_status("Speaking…")
        )
        self._tts.signals.finished.connect(
            lambda: self._set_status("")
        )
        self._tts.signals.error.connect(
            lambda msg: Toast.show_message(self, f"TTS Error: {msg}", "error")
        )

    # ════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ════════════════════════════════════════════════════════════════════

    def _on_source_text_changed(self, _text: str) -> None:
        """Re-arm the debounce timer if auto-translate is on."""
        if self._auto_cb.isChecked():
            self._debouncer.trigger()

    def _do_translate(self) -> None:
        """Launch a translation worker on the thread pool."""
        text = self._source_pane.get_text().strip()
        if not text:
            self._target_pane.clear()
            return

        src = self._src_selector.current_code()
        tgt = self._tgt_selector.current_code()

        if src == tgt and src != "auto":
            self._target_pane.set_text(text)
            return

        self._translate_btn.setEnabled(False)
        self._translate_btn.setText("  Translating…")
        self._set_status("Translating…")

        worker = TranslationWorker(text, src, tgt)
        worker.signals.finished.connect(self._on_translation_done)
        worker.signals.error.connect(self._on_translation_error)
        self._thread_pool.start(worker)

    def _on_translation_done(self, result: TranslationResult) -> None:
        self._target_pane.set_text(result.translated_text)
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("  Translate")
        self._anim_translate.apply_state(0.0)

        # Show provider badge
        self._provider_label.setText(
            f"via {result.provider_name}  ·  {result.elapsed_ms:.0f} ms"
        )
        self._provider_label.setVisible(True)
        self._set_status("")

    def _on_translation_error(self, error_msg: str) -> None:
        self._translate_btn.setEnabled(True)
        self._translate_btn.setText("  Translate")
        self._anim_translate.apply_state(0.0)
        self._set_status("")
        Toast.show_message(self, f"Translation failed: {error_msg}", "error")
        logger.error("Translation error: %s", error_msg)

    def _on_swap(self) -> None:
        """Swap source ↔ target languages and texts."""
        src_code = self._src_selector.current_code()
        tgt_code = self._tgt_selector.current_code()

        if src_code == "auto":
            Toast.show_message(
                self, "Cannot swap when source is Auto Detect", "info"
            )
            return

        src_text = self._source_pane.get_text()
        tgt_text = self._target_pane.get_text()

        self._src_selector.set_language(tgt_code)
        self._tgt_selector.set_language(src_code)
        self._source_pane.set_text(tgt_text)
        self._target_pane.set_text(src_text)

    def _copy_text(self, text: str) -> None:
        if not text.strip():
            Toast.show_message(self, "Nothing to copy", "info")
            return
        copy_to_clipboard(text)
        Toast.show_message(self, "Copied to clipboard!", "success")

    def _speak(self, text: str, lang: str) -> None:
        if not text.strip():
            Toast.show_message(self, "Nothing to speak", "info")
            return
        # Limit TTS to first 500 chars for responsiveness
        tts_text = text[:500]
        self._tts.speak(tts_text, lang)

    # ── Theme toggle ───────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self._is_dark = not self._is_dark
        self._apply_theme()
        self._update_theme_icon()
        notify_theme_changed(self._is_dark)

    def _apply_theme(self) -> None:
        filename = "dark_theme.qss" if self._is_dark else "light_theme.qss"
        qss_path = STYLES_DIR / filename
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as fh:
                QApplication.instance().setStyleSheet(fh.read())

    def _update_theme_icon(self) -> None:
        icon_name = "fa5s.moon" if self._is_dark else "fa5s.sun"
        color = "#EDEDED" if self._is_dark else "#09090B"
        self._theme_btn.setIcon(qta.icon(icon_name, color=color))

    # ── Layout toggle ──────────────────────────────────────────────────

    def _toggle_layout(self) -> None:
        current = self._splitter.orientation()
        icon_name = "fa5s.arrows-alt-v" if current == Qt.Orientation.Horizontal else "fa5s.columns"
        if current == Qt.Orientation.Horizontal:
            self._splitter.setOrientation(Qt.Orientation.Vertical)
            self._layout_btn.setToolTip("Switch to side-by-side layout")
        else:
            self._splitter.setOrientation(Qt.Orientation.Horizontal)
            self._layout_btn.setToolTip("Switch to stacked layout")

        self._anim_layout.icon_name = icon_name
        self._anim_layout.apply_state(0.0)

    # ── Helpers ─────────────────────────────────────────────────────────

    def _set_status(self, msg: str) -> None:
        sb = self.statusBar()
        if msg:
            sb.showMessage(msg)
        else:
            sb.clearMessage()

    def _center(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)
