"""
Translator Pro — Searchable language-selector combo box with smooth hover animation.

Loads language entries from ``config/languages.json`` and provides
type-to-filter search via an editable QComboBox with professional chevron arrow.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QCompleter

from config.settings import LANGUAGES_FILE
from ui.components.anim_effects import AnimatedComboBox


class LanguageSelector(QComboBox):
    """
    Searchable, filterable language dropdown.

    Displays ``"Native Name  (English Name)"`` and stores the ISO-639-1
    code as the item's user-data role.

    Signals
    -------
    language_changed(str)
        Emitted with the new ISO code whenever the user picks a language.
    """

    language_changed = Signal(str)

    def __init__(
        self,
        default_code: str = "en",
        exclude_auto: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._languages = self._load_languages()
        self._populate(exclude_auto)
        self._setup_completer()

        # Select the default language
        self.set_language(default_code)

        # Forward Qt signal → our typed signal
        self.currentIndexChanged.connect(self._on_index_changed)

        # Attach smooth color-changing hover animation
        self._anim = AnimatedComboBox(self)
        self._anim.apply_state(0.0)

    # ── Public API ──────────────────────────────────────────────────────

    def current_code(self) -> str:
        """Return the ISO code of the currently selected language."""
        return self.currentData(Qt.ItemDataRole.UserRole) or "en"

    def set_language(self, code: str) -> None:
        """Programmatically select a language by ISO code."""
        for i in range(self.count()):
            if self.itemData(i, Qt.ItemDataRole.UserRole) == code:
                self.setCurrentIndex(i)
                return

    def current_display(self) -> str:
        """Return the display text of the selected language."""
        return self.currentText()

    # ── Private ─────────────────────────────────────────────────────────

    @staticmethod
    def _load_languages() -> List[dict]:
        """Load the language list from the JSON config file."""
        path = Path(LANGUAGES_FILE)
        if not path.exists():
            return [{"code": "en", "name": "English", "native": "English"}]
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def _populate(self, exclude_auto: bool) -> None:
        """Fill the combo box items."""
        for entry in self._languages:
            code = entry["code"]
            if exclude_auto and code == "auto":
                continue
            display = f'{entry["native"]}  ({entry["name"]})'
            self.addItem(display, userData=code)

    def _setup_completer(self) -> None:
        """Attach a case-insensitive completer for type-to-search."""
        completer = QCompleter(
            [self.itemText(i) for i in range(self.count())], self
        )
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(completer)

    def _on_index_changed(self, _index: int) -> None:
        code = self.current_code()
        if code:
            self.language_changed.emit(code)
