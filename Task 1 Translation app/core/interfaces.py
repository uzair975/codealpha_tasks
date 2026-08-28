"""
Translator Pro — Abstract interfaces for the service layer.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TranslationResult:
    """Immutable container for a single translation response."""
    translated_text: str
    source_lang: str
    target_lang: str
    provider_name: str = ""
    elapsed_ms: float = 0.0
    detected_lang: str | None = None          # populated when src='auto'
    is_fallback: bool = False


class ITranslationProvider(ABC):
    """
    Contract that every translation backend must satisfy.
    Implementations: GoogleProvider, DeepLProvider, etc.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name (e.g. 'Google Translate')."""
        ...

    @abstractmethod
    def translate(self, text: str, src: str, tgt: str) -> TranslationResult:
        """
        Translate *text* from *src* language code to *tgt* language code.

        Parameters
        ----------
        text : str
            Source text (may be multi-paragraph).
        src : str
            ISO-639-1 source language code, or ``'auto'`` for detection.
        tgt : str
            ISO-639-1 target language code.

        Returns
        -------
        TranslationResult

        Raises
        ------
        ConnectionError
            Network unreachable or timeout.
        RuntimeError
            Provider returned an error (rate-limit, bad request, etc.).
        """
        ...

    @abstractmethod
    def supports(self, lang_code: str) -> bool:
        """Return True if the provider can handle the given language code."""
        ...
