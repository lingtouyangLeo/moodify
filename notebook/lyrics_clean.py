import os
import re
import string
import pandas as pd

# Try to import langdetect for language identification
try:
    from langdetect import detect_langs, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException

    # Fix seed to make detection results deterministic
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


# ============ 1. CONFIGURATION ============

# Directory of this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Project root = parent directory of current file
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Input / Output CSV paths
INPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics.csv")
OUTPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics_cleaned.csv")

# Remove bracket comments like [Chorus], [Verse 1]
REMOVE_SQUARE_BRACKET_COMMENTS = True
# Remove stage/direction comments in parentheses: (Verse), (Chorus), (Bridge)
REMOVE_STAGE_COMMENTS = True
# Remove URLs in lyrics
REMOVE_URLS = True

# Minimum cleaned lyric length; rows below this threshold will be dropped
MIN_CLEAN_LENGTH = 20

# Minimum probability for langdetect to consider the text as English
LANGDETECT_EN_PROB_THRESHOLD = 0.90


# ============ 2. UTILITY FUNCTIONS ============

def is_stage_comment(text: str) -> bool:
    """
    Determine whether the parentheses content is a stage direction,
    such as (Verse), (Chorus), (Intro), (Bridge), etc.
    If true → remove; otherwise keep (e.g., emotional cues like (yeah), (oh no)).
    """
    if not text:
        return False

    lowered = text.lower().strip()

    # Common structural/stage keywords
    keywords = [
        "verse", "chorus", "bridge", "intro", "outro",
        "pre-chorus", "pre chorus", "hook",
        "refrain", "post-chorus", "post chorus",
        "instrumental", "solo"
    ]

    # Contains structural markers like "verse 1", "chorus 2"
    for kw in keywords:
        if kw in lowered:
            return True

    # Very short tokens like (v1), (c), (b) → likely structure markers
    if len(lowered) <= 4 and all(ch.isalnum() or ch.isspace() for ch in lowered):
        return True

    return False


def is_english_langdetect(text: str,
                          prob_threshold: float = LANGDETECT_EN_PROB_THRESHOLD) -> bool:
    """
    Use langdetect to decide whether the given text is English.

    Logic:
        - Use detect_langs(text) to get language probabilities
        - If 'en' appears and its probability >= prob_threshold → consider it English
        - If detection fails or langdetect is not available → return False

    Args:
        text: Lyrics text
        prob_threshold: minimum probability for English

    Returns:
        bool: True if text is considered English, False otherwise
    """
    if not LANGDETECT_AVAILABLE:
        # If langdetect is not installed, we fail closed (treat as non-English)
        return False

    if text is None:
        return False

    # Convert to string and strip
    text = str(text).strip()
    if not text:
        return False

    # langdetect works better with a bit of length; short strings are unreliable
    # You can tweak this if you want to keep very short lyrics
    if len(text) < 20:
        return False

    try:
        langs = detect_langs(text)
    except LangDetectException:
        # Happens when text is too short or not informative
        return False

    for lang_prob in langs:
        # lang_prob is something like: "en:0.999996"
        if lang_prob.lang == "en" and lang_prob.prob >= prob_threshold:
            return True

    return False


def clean_lyrics_one_song(raw_lyrics: str) -> str:
    """
    Clean the lyrics of a single song.

    Steps:
        1. Normalize line breaks
        2. Process line by line:
           - Remove URLs
           - Remove [Verse], [Chorus] sections
           - Remove stage comments like (Chorus)
           - Keep emotional cues like (yeah)
        3. Convert to lowercase
        4. Keep only allowed characters (letters, digits, basic punctuation)
        5. Collapse extra spaces and blank lines
    """
    if pd.isna(raw_lyrics):
        return ""

    text = str(raw_lyrics)

    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove URLs
        if REMOVE_URLS:
            line = re.sub(r"http\S+|www\.\S+", "", line).strip()
            if line == "":
                continue

        # Remove [Chorus], [Verse], etc.
        if REMOVE_SQUARE_BRACKET_COMMENTS:
            line = re.sub(r"\[.*?\]", "", line).strip()
            if line == "":
                continue

        # Remove (Verse), (Chorus) but keep emotional parentheses
        if REMOVE_STAGE_COMMENTS:
            def _handle_paren(m):
                inner = m.group(1)
                if is_stage_comment(inner):
                    return ""  # remove stage comment
                else:
                    return m.group(0)  # keep emotional/textual parentheses

            line = re.sub(r"\((.*?)\)", _handle_paren, line).strip()
            if line == "":
                continue

        cleaned_lines.append(line)

    joined = "\n".join(cleaned_lines)

    # Lowercase
    joined = joined.lower()

    # Keep letters, digits, basic punctuation, spaces, newlines
    joined = re.sub(r"[^a-z0-9\s\.\,\!\?\'\"\n]", " ", joined)

    # Collapse multiple spaces
    joined = re.sub(r"[ \t]+", " ", joined)
    # Collapse multiple blank lines
    joined = re.sub(r"\n{2,}", "\n", joined)

    return joined.strip()


# ============ 3. MAIN EXECUTION ============

if __name__ == "__main__":
    if not LANGDETECT_AVAILABLE:
        raise ImportError(
            "langdetect is not installed. Please install it first:\n\n"
            "    pip install langdetect\n"
        )

    print(f"Reading CSV: {INPUT_CSV_PATH}")
    if not os.path.exists(INPUT_CSV_PATH):
        raise FileNotFoundError(f"Input CSV not found at: {INPUT_CSV_PATH}")

    df = pd.read_csv(INPUT_CSV_PATH)

    if "lyrics" not in df.columns:
        raise ValueError("The CSV does not contain the column 'lyrics'. Please check the file.")

    # Drop rows with NaN lyrics early
    df = df[df["lyrics"].notna()].reset_index(drop=True)

    # 1️⃣ Keep only English songs based on langdetect
    print("Detecting language with langdetect and filtering to English songs only...")
    df["is_english"] = df["lyrics"].apply(is_english_langdetect)
    df = df[df["is_english"]].reset_index(drop=True)
    df = df.drop(columns=["is_english"])

    print(f"Remaining rows after English filtering: {len(df)}")

    if len(df) == 0:
        raise ValueError(
            "No English songs remain after langdetect-based filtering. "
            "You may want to lower LANGDETECT_EN_PROB_THRESHOLD or inspect the data."
        )

    # 2️⃣ Clean lyrics
    print("Cleaning lyrics...")
    df["clean_lyrics"] = df["lyrics"].apply(clean_lyrics_one_song)

    # 3️⃣ Drop empty or very short clean lyrics
    df = df[df["clean_lyrics"].notna()]
    df["clean_lyrics"] = df["clean_lyrics"].astype(str).str.strip()
    df = df[df["clean_lyrics"] != ""]
    df = df[df["clean_lyrics"].str.len() >= MIN_CLEAN_LENGTH].reset_index(drop=True)

    print(f"Remaining rows after cleaning: {len(df)}")

    if len(df) == 0:
        raise ValueError(
            "All songs were removed after cleaning. "
            "Adjust cleaning rules or MIN_CLEAN_LENGTH."
        )

    # 4️⃣ Keep relevant columns if they exist
    keep_cols = []
    for col in ["track_name", "artist_name", "play_count", "lyrics", "clean_lyrics"]:
        if col in df.columns:
            keep_cols.append(col)

    if not keep_cols:
        keep_cols = ["clean_lyrics"]

    df = df[keep_cols]

    # 5️⃣ Save cleaned CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df.to_csv(OUTPUT_CSV_PATH, index=False)

    print(f"Saved cleaned CSV to: {OUTPUT_CSV_PATH}")
    print("Preview:")
    print(df.head())
