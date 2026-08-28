"""
Translator Pro — QRunnable worker classes for off-main-thread work.

Workers use a lightweight QObject signal bridge because QRunnable
does not inherit QObject and cannot emit signals directly.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from core.interfaces import TranslationResult
from core.translator_engine import TranslationPipeline
from core.tts_engine import TTSManager


# ────────────────────────────────────────────────────────────────────────
#  Signal bridges
# ────────────────────────────────────────────────────────────────────────

class TranslationSignals(QObject):
    """Signals emitted by ``TranslationWorker``."""
    finished = Signal(TranslationResult)
    error = Signal(str)


class TTSSignals(QObject):
    """Signals emitted by ``TTSWorker``."""
    started = Signal()
    finished = Signal()
    error = Signal(str)


# ────────────────────────────────────────────────────────────────────────
#  Translation Worker
# ────────────────────────────────────────────────────────────────────────

class TranslationWorker(QRunnable):
    """
    Runs a translation request on the QThreadPool and emits the result
    via ``signals.finished`` or ``signals.error``.
    """

    def __init__(self, text: str, src: str, tgt: str):
        super().__init__()
        self.text = text
        self.src = src
        self.tgt = tgt
        self.signals = TranslationSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            pipeline = TranslationPipeline()
            result = pipeline.translate(self.text, self.src, self.tgt)
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


# ────────────────────────────────────────────────────────────────────────
#  TTS Worker
# ────────────────────────────────────────────────────────────────────────

class TTSWorker(QRunnable):
    """
    Enqueues a TTS request to the singleton ``TTSManager``.
    The TTSManager's own daemon thread handles the actual synthesis.
    """

    def __init__(self, text: str, lang: str = "en"):
        super().__init__()
        self.text = text
        self.lang = lang
        self.signals = TTSSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            tts = TTSManager()
            self.signals.started.emit()
            tts.speak(self.text, self.lang)
            # Note: speak() just enqueues — actual playback is async in the daemon.
            self.signals.finished.emit()
        except Exception as exc:
            self.signals.error.emit(str(exc))
