"""
Translator Pro — Thread-safe TTS manager.

Primary:  gTTS  → temp .mp3 → pygame.mixer playback  (online, natural voice).
Fallback: pyttsx3  → offline system voices.

Runs a persistent daemon-thread consumer loop so the UI never blocks.
Emits Qt signals via a lightweight QObject bridge.
"""
from __future__ import annotations

import logging
import os
import queue
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from config.settings import TTS_RATE, TTS_VOLUME, TTS_TEMP_DIR

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────
#  Signal bridge (lives on main thread, emits to UI)
# ────────────────────────────────────────────────────────────────────────

class TTSSignals(QObject):
    """Qt signals emitted by the TTS daemon."""
    started = Signal()
    finished = Signal()
    error = Signal(str)


# ────────────────────────────────────────────────────────────────────────
#  Request dataclass
# ────────────────────────────────────────────────────────────────────────

@dataclass
class TTSRequest:
    text: str
    lang: str           # ISO-639-1 code (e.g. "es", "fr")
    stop: bool = False  # sentinel to shut down the daemon


# ────────────────────────────────────────────────────────────────────────
#  TTS Manager (singleton-ish)
# ────────────────────────────────────────────────────────────────────────

class TTSManager:
    """
    Thread-safe TTS orchestrator.

    Usage::

        tts = TTSManager()
        tts.speak("Hola mundo", "es")
        tts.signals.started.connect(on_start)
        tts.signals.finished.connect(on_finish)
    """

    _instance: TTSManager | None = None

    def __new__(cls) -> TTSManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialised = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True

        self.signals = TTSSignals()
        self._queue: queue.Queue[TTSRequest] = queue.Queue()
        self._mixer_ready = False

        # Ensure temp dir exists
        TTS_TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Start daemon thread
        self._thread = threading.Thread(
            target=self._consumer_loop, daemon=True, name="tts-daemon"
        )
        self._thread.start()

    # ── public API ──────────────────────────────────────────────────────

    def speak(self, text: str, lang: str = "en") -> None:
        """Enqueue a TTS request (non-blocking)."""
        self._queue.put(TTSRequest(text=text, lang=lang))

    def stop(self) -> None:
        """Send a stop sentinel to gracefully exit the daemon."""
        self._queue.put(TTSRequest(text="", lang="", stop=True))

    # ── daemon consumer ────────────────────────────────────────────────

    def _consumer_loop(self) -> None:
        """Blocking loop that processes TTS requests sequentially."""
        while True:
            request = self._queue.get()
            if request.stop:
                logger.info("TTS daemon shutting down.")
                break
            self._process(request)
            self._queue.task_done()

    def _process(self, req: TTSRequest) -> None:
        self.signals.started.emit()
        try:
            self._speak_gtts(req.text, req.lang)
        except Exception as gtts_err:
            logger.warning("gTTS failed (%s), falling back to pyttsx3.", gtts_err)
            try:
                self._speak_pyttsx3(req.text, req.lang)
            except Exception as pyttsx3_err:
                logger.error("pyttsx3 also failed: %s", pyttsx3_err)
                self.signals.error.emit(str(pyttsx3_err))
                return
        self.signals.finished.emit()

    # ── gTTS (online, high quality) ────────────────────────────────────

    def _speak_gtts(self, text: str, lang: str) -> None:
        from gtts import gTTS

        tmp_path = TTS_TEMP_DIR / f"tts_{threading.get_ident()}.mp3"
        tts = gTTS(text=text, lang=lang if lang != "auto" else "en")
        tts.save(str(tmp_path))
        self._play_mp3(str(tmp_path))

    def _play_mp3(self, path: str) -> None:
        """Play an mp3 file using pygame.mixer."""
        import pygame

        if not self._mixer_ready:
            pygame.mixer.init()
            self._mixer_ready = True

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)

        # Cleanup
        try:
            pygame.mixer.music.unload()
            os.remove(path)
        except Exception:
            pass

    # ── pyttsx3 (offline fallback) ─────────────────────────────────────

    def _speak_pyttsx3(self, text: str, lang: str) -> None:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", TTS_RATE)
        engine.setProperty("volume", TTS_VOLUME)

        # Try to match a voice for the target language
        voices = engine.getProperty("voices")
        for voice in voices:
            # Voice ids often contain the language code
            if lang.lower() in voice.id.lower() or lang.lower() in (voice.name or "").lower():
                engine.setProperty("voice", voice.id)
                break

        engine.say(text)
        engine.runAndWait()
        engine.stop()
