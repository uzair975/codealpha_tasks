"""
Translator Pro — Translation engine with provider fallback pipeline.

Primary: Google Translate (Direct Chrome RPC endpoint + deep_translator fallback).
Secondary: MyMemory Translate (free backup provider).
Optional: DeepL (if API key is configured in .env).
Handles character-splitting for long inputs (>5 000 chars).
"""
from __future__ import annotations

import logging
import time
from typing import List

import requests
from deep_translator import GoogleTranslator

from config.settings import DEEPL_API_KEY, MAX_CHUNK_CHARS
from core.interfaces import ITranslationProvider, TranslationResult

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────
#  Google Provider (free, zero-config, highly reliable)
# ────────────────────────────────────────────────────────────────────────

class GoogleProvider(ITranslationProvider):
    """High-reliability Google Translate provider with direct RPC + web fallback."""

    @property
    def name(self) -> str:
        return "Google Translate"

    def translate(self, text: str, src: str, tgt: str) -> TranslationResult:
        t0 = time.perf_counter()

        # 1. Direct Chrome Extension RPC endpoint (never 429 rate-limited)
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "dict-chrome-ex",
                "sl": src,
                "tl": tgt,
                "dt": "t",
                "q": text,
            }
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                translated_parts = [item[0] for item in data[0] if item and item[0]]
                result_text = "".join(translated_parts)
                elapsed = (time.perf_counter() - t0) * 1000
                return TranslationResult(
                    translated_text=result_text,
                    source_lang=src,
                    target_lang=tgt,
                    provider_name=self.name,
                    elapsed_ms=round(elapsed, 1),
                )
        except Exception as exc:
            logger.warning("Direct Google API call failed (%s), falling back to deep_translator.", exc)

        # 2. Secondary fallback: deep_translator.GoogleTranslator with retry
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                translator = GoogleTranslator(source=src, target=tgt)
                result_text = translator.translate(text)
                elapsed = (time.perf_counter() - t0) * 1000
                return TranslationResult(
                    translated_text=result_text or "",
                    source_lang=src,
                    target_lang=tgt,
                    provider_name=self.name,
                    elapsed_ms=round(elapsed, 1),
                )
            except Exception as exc:
                last_exc = exc
                if attempt == 0:
                    time.sleep(0.3)

        raise last_exc or RuntimeError("Google Translate provider failed.")

    def supports(self, lang_code: str) -> bool:
        return True


# ────────────────────────────────────────────────────────────────────────
#  MyMemory Provider (free backup provider)
# ────────────────────────────────────────────────────────────────────────

class MyMemoryProvider(ITranslationProvider):
    """Free MyMemory fallback translation provider."""

    @property
    def name(self) -> str:
        return "MyMemory"

    def translate(self, text: str, src: str, tgt: str) -> TranslationResult:
        from deep_translator import MyMemoryTranslator

        t0 = time.perf_counter()
        s_code = "en-US" if src in ("en", "auto") else src
        t_code = "ur-PK" if tgt == "ur" else tgt

        translator = MyMemoryTranslator(source=s_code, target=t_code)
        result_text = translator.translate(text)
        elapsed = (time.perf_counter() - t0) * 1000
        return TranslationResult(
            translated_text=result_text or "",
            source_lang=src,
            target_lang=tgt,
            provider_name=self.name,
            elapsed_ms=round(elapsed, 1),
        )

    def supports(self, lang_code: str) -> bool:
        return True


# ────────────────────────────────────────────────────────────────────────
#  DeepL Provider (optional, requires API key)
# ────────────────────────────────────────────────────────────────────────

class DeepLProvider(ITranslationProvider):
    """Wraps ``deep_translator.DeeplTranslator``. Only available if key is set."""

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or DEEPL_API_KEY

    @property
    def name(self) -> str:
        return "DeepL"

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def translate(self, text: str, src: str, tgt: str) -> TranslationResult:
        if not self.available:
            raise RuntimeError("DeepL API key not configured.")

        from deep_translator import DeeplTranslator

        t0 = time.perf_counter()
        translator = DeeplTranslator(
            api_key=self._api_key,
            source=src.upper() if src != "auto" else "auto",
            target=tgt.upper(),
        )
        result_text = translator.translate(text)
        elapsed = (time.perf_counter() - t0) * 1000
        return TranslationResult(
            translated_text=result_text or "",
            source_lang=src,
            target_lang=tgt,
            provider_name=self.name,
            elapsed_ms=round(elapsed, 1),
        )

    def supports(self, lang_code: str) -> bool:
        return self.available


# ────────────────────────────────────────────────────────────────────────
#  Translation Pipeline (primary → fallback + chunking)
# ────────────────────────────────────────────────────────────────────────

class TranslationPipeline:
    """
    Orchestrates translation through a chain of providers.

    * Automatically splits long texts into paragraph-aligned chunks.
    * Falls back to the next provider on network / rate-limit errors.
    """

    def __init__(self, providers: List[ITranslationProvider] | None = None):
        if providers is None:
            providers = self._default_chain()
        self._providers = providers

    # ── public ──────────────────────────────────────────────────────────

    def translate(self, text: str, src: str, tgt: str) -> TranslationResult:
        """Translate, with chunking and fallback."""
        if not text or not text.strip():
            return TranslationResult("", src, tgt)

        chunks = self._split(text)
        last_error: Exception | None = None

        for provider in self._providers:
            try:
                translated_chunks: list[str] = []
                total_ms = 0.0
                for chunk in chunks:
                    r = provider.translate(chunk, src, tgt)
                    translated_chunks.append(r.translated_text)
                    total_ms += r.elapsed_ms

                return TranslationResult(
                    translated_text="\n\n".join(translated_chunks),
                    source_lang=src,
                    target_lang=tgt,
                    provider_name=provider.name,
                    elapsed_ms=round(total_ms, 1),
                    is_fallback=provider is not self._providers[0],
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Provider %s failed: %s — trying next.", provider.name, exc
                )

        raise ConnectionError(
            f"All translation providers failed. Last error: {last_error}"
        )

    # ── private ─────────────────────────────────────────────────────────

    @staticmethod
    def _default_chain() -> List[ITranslationProvider]:
        """Build the default provider chain: DeepL (if key) → Google → MyMemory."""
        chain: list[ITranslationProvider] = []
        deepl = DeepLProvider()
        if deepl.available:
            chain.append(deepl)
        chain.append(GoogleProvider())
        chain.append(MyMemoryProvider())
        return chain

    @staticmethod
    def _split(text: str) -> list[str]:
        """Split *text* into chunks ≤ MAX_CHUNK_CHARS, breaking on paragraphs."""
        if len(text) <= MAX_CHUNK_CHARS:
            return [text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para) + 2
            if current_len + para_len > MAX_CHUNK_CHARS and current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            current.append(para)
            current_len += para_len

        if current:
            chunks.append("\n\n".join(current))

        return chunks

