"""
Translator Pro — Application Settings & Constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Paths ───────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = APP_DIR / "assets"
STYLES_DIR = ASSETS_DIR / "styles"
CONFIG_DIR = APP_DIR / "config"
LANGUAGES_FILE = CONFIG_DIR / "languages.json"

# ── Load .env (optional API keys) ──────────────────────────────────────
load_dotenv(APP_DIR / ".env")

DEEPL_API_KEY: str = os.getenv("DEEPL_API_KEY", "")
GOOGLE_CLOUD_API_KEY: str = os.getenv("GOOGLE_CLOUD_API_KEY", "")

# ── Translation Settings ───────────────────────────────────────────────
DEFAULT_SOURCE_LANG = "en"
DEFAULT_TARGET_LANG = "es"
MAX_CHUNK_CHARS = 5000          # Max characters per API call
DEBOUNCE_DELAY_MS = 500         # Milliseconds to wait after last keystroke

# ── TTS Settings ───────────────────────────────────────────────────────
TTS_RATE = 160                  # Words-per-minute for pyttsx3
TTS_VOLUME = 0.9                # 0.0 – 1.0
TTS_TEMP_DIR = APP_DIR / ".tts_cache"

# ── UI Constants ───────────────────────────────────────────────────────
WINDOW_TITLE = "Translator Pro"
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 620
TOAST_DURATION_MS = 2500
