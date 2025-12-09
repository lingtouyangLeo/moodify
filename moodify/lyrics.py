import re
import os
from typing import Tuple, List, Dict, Any

# lyricsgenius 可能未安装，避免导入报错
try:
    import lyricsgenius
except ImportError:  # pragma: no cover
    lyricsgenius = None

# 可选的 pandas，用于处理缺失值；不存在时用 None 代替
try:
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover
    pd = None

# ======== Genius 歌词配置 ========
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

# ======== 歌词清洗逻辑（与 notebook/lyrics_clean.py 保持一致） ========
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
    "chorus",
    "verse",
    "bridge",
    "hook",
    "intro",
    "outro",
    "pre-chorus",
    "post-chorus",
    "background",
    "vocals",
    "beat",
    "instrumental",
    "guitar",
    "solo",
    "spoken",
    "talking",
    "whisper",
    "laughs",
    "applause",
    "crowd",
]

TO_LOWER = True
REMOVE_STAGE_COMMENTS = True


def _is_na(val) -> bool:
    if pd is not None:
        return bool(pd.isna(val))
    return val is None


def is_stage_comment(text: str) -> bool:
    t = text.strip().lower()
    if len(t.split()) > 6:
        return True
    return any(k in t for k in STAGE_COMMENT_KEYWORDS)


def clean_lyrics_one_song(text: str) -> str:
    if _is_na(text):
        return ""

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line == "":
            continue

        lower_line = line.lower()
        if any(k in lower_line for k in BAD_KEYWORDS):
            continue

        if SECTION_HEADER_PATTERN.match(line):
            continue

        if REMOVE_STAGE_COMMENTS and line.startswith("(") and line.endswith(")"):
            inner = line[1:-1]
            if is_stage_comment(inner):
                continue

        if REMOVE_STAGE_COMMENTS:
            def _handle_paren(m):
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

    merged_lines = []
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]
        if (
            len(line) == 1
            and line in {",", ".", "!", "?", ";", ":"}
            and i > 0
            and i < len(cleaned_lines) - 1
        ):
            prev_line = merged_lines.pop()
            next_line = cleaned_lines[i + 1]
            merged_lines.append(prev_line.rstrip() + line + " " + next_line.lstrip())
            i += 2
        else:
            merged_lines.append(line)
            i += 1

    text = "\n".join(merged_lines)
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
    )
    text = re.sub(r"[ \t]+", " ", text)
    if TO_LOWER:
        text = text.lower()
    return text.strip()


def fetch_lyrics(track_name: str, artist_name: str) -> Tuple[str, str]:
    if genius_client is None:
        return None, "Genius client is not initialized (missing token or lyricsgenius not installed)."
    try:
        song = genius_client.search_song(track_name, artist_name)
        if song and isinstance(song.lyrics, str) and song.lyrics.strip():
            return song.lyrics, None
        return None, "Lyrics not found or empty."
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def process_recent_tracks(recent_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """根据 recent_list 拉取并清洗歌词，返回带 clean_lyrics 的列表"""
    processed = []
    for item in recent_list:
        track_name = item.get("track_name")
        artist_name = item.get("artist_name")
        lyrics, err = fetch_lyrics(track_name, artist_name)
        clean_lyrics = clean_lyrics_one_song(lyrics) if lyrics else ""
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
