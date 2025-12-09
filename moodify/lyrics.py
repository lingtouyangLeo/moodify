import re
import os
from typing import Tuple, List, Dict, Any

# lyricsgenius may not be installed; avoid hard failure on import
try:
    import lyricsgenius
except ImportError:  # pragma: no cover
    lyricsgenius = None

# Optional pandas, used only for NA handling
try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover
    pd = None

# Try to import langdetect for language identification (mirrors notebook/lyrics_clean.py)
try:  # pragma: no cover - optional dependency
    from langdetect import detect_langs, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException

    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:  # pragma: no cover
    LANGDETECT_AVAILABLE = False

# ======== Genius lyrics configuration ========
GENIUS_ACCESS_TOKEN = "3AhYPPIL5RQbybxGO0UvFk2OH_ZHkiN6w07CVwy9WNrLzxN0qhBDW2rIRkV8041e"
GENIUS_TIMEOUT = 15

if GENIUS_ACCESS_TOKEN and lyricsgenius:
    genius_client = lyricsgenius.Genius(
        GENIUS_ACCESS_TOKEN,
        timeout=GENIUS_TIMEOUT,
        skip_non_songs=True,
        remove_section_headers=True,
    )
else:
    genius_client = None

# ======== Cleaning configuration (aligned with notebook/lyrics_clean.py) ========
REMOVE_SQUARE_BRACKET_COMMENTS = True
REMOVE_STAGE_COMMENTS = True
REMOVE_URLS = True
MIN_CLEAN_LENGTH = 20
LANGDETECT_EN_PROB_THRESHOLD = 0.90

BAD_KEYWORDS = [
    "you might also like",
    "embed",
    "track info",
    "more on genius",
    "lyrics powered by",
    "produced by",
    "written by",
    "composed by",
    "recorded at",
    "mastered by",
    "engineered by",
]

SECTION_HEADER_PATTERN = re.compile(r"^\s*\[.*?\]\s*$")

STAGE_COMMENT_KEYWORDS = [
    "verse",
    "chorus",
    "bridge",
    "intro",
    "outro",
    "pre-chorus",
    "pre chorus",
    "hook",
    "refrain",
    "post-chorus",
    "post chorus",
    "instrumental",
    "solo",
]

TO_LOWER = True


def _is_na(val) -> bool:
    if pd is not None:
        return bool(pd.isna(val))
    return val is None


def is_stage_comment(text: str) -> bool:
    """Return True if the parentheses content is a structural/stage direction.

    This mirrors the behavior in notebook/lyrics_clean.py: phrases like
    "(Verse 1)", "(Chorus)" and short tokens like (v1) are treated as
    stage comments and removed, while emotional cues like (yeah) are kept.
    """
    if not text:
        return False

    lowered = text.lower().strip()

    keywords = STAGE_COMMENT_KEYWORDS

    for kw in keywords:
        if kw in lowered:
            return True

    if len(lowered) <= 4 and all(ch.isalnum() or ch.isspace() for ch in lowered):
        return True

    return False


def is_english_langdetect(text: str, prob_threshold: float = LANGDETECT_EN_PROB_THRESHOLD) -> bool:
    """Use langdetect to decide whether the given lyrics text is English.

    If langdetect is not installed or the text is too short / invalid,
    this function returns False.
    """
    if not LANGDETECT_AVAILABLE:
        return False

    if text is None:
        return False

    text = str(text).strip()
    if not text:
        return False

    if len(text) < 20:
        return False

    try:  # pragma: no cover - depends on langdetect
        langs = detect_langs(text)
    except Exception:  # includes LangDetectException
        return False

    for lang_prob in langs:
        if getattr(lang_prob, "lang", None) == "en" and getattr(lang_prob, "prob", 0.0) >= prob_threshold:
            return True

    return False


def clean_lyrics_one_song(raw_lyrics: str) -> str:
    """Clean lyrics for a single song.

    This implementation is based on notebook/lyrics_clean.py and performs:
    - line normalization
    - URL removal
    - removal of [Chorus], [Verse] style headers
    - removal of stage comments in parentheses while keeping emotional ones
    - keyword-based garbage line filtering
    - lowercasing and character filtering
    """
    if _is_na(raw_lyrics):
        return ""

    text = str(raw_lyrics)

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    cleaned_lines: List[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if REMOVE_URLS:
            line = re.sub(r"http\S+|www\.\S+", "", line).strip()
            if line == "":
                continue

        lower_line = line.lower()
        if any(k in lower_line for k in BAD_KEYWORDS):
            continue

        if REMOVE_SQUARE_BRACKET_COMMENTS:
            if SECTION_HEADER_PATTERN.match(line):
                continue
            line = re.sub(r"\[.*?\]", "", line).strip()
            if line == "":
                continue

        if REMOVE_STAGE_COMMENTS:
            def _handle_paren(m: re.Match) -> str:
                inner = m.group(1)
                if is_stage_comment(inner):
                    return ""
                return m.group(0)

            line = re.sub(r"\((.*?)\)", _handle_paren, line).strip()
            if line == "":
                continue

        cleaned_lines.append(line)

    if not cleaned_lines:
        return ""

    joined = "\n".join(cleaned_lines)

    joined = joined.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')

    if TO_LOWER:
        joined = joined.lower()

    joined = re.sub(r"[^a-z0-9\s\.\,\!\?\'\"\n]", " ", joined)

    joined = re.sub(r"[ \t]+", " ", joined)
    joined = re.sub(r"\n{2,}", "\n", joined)

    return joined.strip()


def fetch_lyrics(track_name: str, artist_name: str) -> Tuple[str | None, str | None]:
    """Fetch raw lyrics for a track using the Genius API.

    Returns a tuple (lyrics, error_message). If lyrics is None, error_message
    contains a human-readable description in English.
    """
    if genius_client is None:
        return None, "Genius client is not initialized (missing GENIUS_ACCESS_TOKEN or lyricsgenius not installed)."
    try:  # pragma: no cover - external HTTP
        song = genius_client.search_song(track_name, artist_name)
        if song and isinstance(song.lyrics, str) and song.lyrics.strip():
            return song.lyrics, None
        return None, "Lyrics not found or empty."
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def process_recent_tracks(recent_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fetch and clean lyrics for a list of recent tracks.

    For each item in recent_list (expected keys: track_name, artist_name),
    this function fetches lyrics via Genius, cleans them using
    clean_lyrics_one_song, and returns a new list including
    "lyrics", "clean_lyrics", and "error" fields.
    """
    processed: List[Dict[str, Any]] = []
    for item in recent_list:
        track_name = item.get("track_name")
        artist_name = item.get("artist_name")
        lyrics, err = fetch_lyrics(track_name, artist_name)
        clean_lyrics = clean_lyrics_one_song(lyrics) if lyrics else ""

        if clean_lyrics and len(clean_lyrics) < MIN_CLEAN_LENGTH:
            err = (err or "") + " | Cleaned lyrics too short"

        processed.append(
            {
                "track_name": track_name,
                "artist_name": artist_name,
                "lyrics": lyrics,
                "clean_lyrics": clean_lyrics,
                "error": err,
            }
        )
    return processed
