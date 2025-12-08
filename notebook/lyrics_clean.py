# If you are on Colab, make sure pandas is installed
# !pip install pandas

import pandas as pd
import re

# ============ 1. Configuration Section (modify as needed) ============


import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

INPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics.csv")
OUTPUT_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics_cleaned.csv")


# Whether to convert lyrics to lowercase (recommended: True, helpful for sentiment classification & vectorization)
TO_LOWER = True

# Whether to remove “stage-direction style text” in parentheses (but keep emotional shouts)
# Examples removed: (Chorus), (Verse 2), (Bridge), (Background Vocals)
# Examples kept: (yeah), (oh no)
REMOVE_STAGE_COMMENTS = True


# ============ 2. Patterns and Keywords ============

# Non-lyrics / website hints / production info etc. (matched after lowercasing)
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

# [Chorus] / [Verse 1] / [Bridge] etc. section labels
SECTION_HEADER_PATTERN = re.compile(r"^\s*\[.*?\]\s*$")

# Typical keywords indicating “stage-direction style” parenthetical content
STAGE_COMMENT_KEYWORDS = [
    "chorus", "verse", "bridge", "hook", "intro", "outro",
    "pre-chorus", "post-chorus",
    "background", "vocals", "beat", "instrumental",
    "guitar", "solo", "spoken", "talking", "whisper",
    "laughs", "applause", "crowd",
]


def is_stage_comment(text: str) -> bool:
    """
    Determine whether the content inside parentheses is stage direction
    rather than an emotional shout.
    Example: Chorus, Background Vocals -> True
             yeah, oh no -> False
    """
    t = text.strip().lower()
    # Very long descriptions are usually stage directions (e.g., background talking…)
    if len(t.split()) > 6:
        return True
    return any(k in t for k in STAGE_COMMENT_KEYWORDS)


def clean_lyrics_one_song(text: str) -> str:
    """Clean lyrics for a single song and return the cleaned string"""
    if pd.isna(text):
        return text

    # -------- 2.1 Split lines and process line-by-line --------
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        original_line = line
        line = line.strip()

        # Skip empty lines (will normalize later)
        if line == "":
            continue

        lower_line = line.lower()

        # ① Remove clearly non-lyric garbage lines (hints / credits)
        if any(k in lower_line for k in BAD_KEYWORDS):
            continue

        # ② Remove structural labels like [Chorus] / [Verse 1]
        if SECTION_HEADER_PATTERN.match(line):
            continue

        # ③ Optionally remove whole-line stage comments in parentheses
        #    Examples: (Chorus), (Bridge), (Background Vocals)
        if REMOVE_STAGE_COMMENTS and line.startswith("(") and line.endswith(")"):
            inner = line[1:-1]
            if is_stage_comment(inner):
                # This is something like (Chorus) → drop entire line
                continue

        # ④ Parentheses inside the line: remove stage comments but keep emotional shouts
        #    Example kept: I said (yeah!) I love you
        #    Example removed: (Background Vocals: la la la)
        if REMOVE_STAGE_COMMENTS:
            def _handle_paren(m):
                inner = m.group(1)
                if is_stage_comment(inner):
                    # Remove stage-direction parentheses
                    return ""
                else:
                    # Keep emotional parentheses (e.g., (yeah), (oh no))
                    return m.group(0)

            line = re.sub(r"\((.*?)\)", _handle_paren, line).strip()
            if line == "":
                continue

        cleaned_lines.append(line)

    # If everything was removed, return empty string
    if not cleaned_lines:
        return ""

    # -------- 2.2 Merge broken punctuation-only lines (simple version) --------
    merged_lines = []
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]

        # If line contains only punctuation and is between two non-empty lines → merge
        if (
            len(line) == 1
            and line in {",", ".", "!", "?", ";", ":"}
            and i > 0
            and i < len(cleaned_lines) - 1
        ):
            prev_line = merged_lines.pop()
            next_line = cleaned_lines[i + 1]
            merged = prev_line.rstrip() + line + " " + next_line.lstrip()
            merged_lines.append(merged)
            i += 2  # Skip next line
        else:
            merged_lines.append(line)
            i += 1

    text = "\n".join(merged_lines)

    # -------- 2.3 Normalize symbols, whitespace, casing --------
    # Normalize various quotation marks
    text = (
        text.replace("’", "'")
            .replace("‘", "'")
            .replace("“", '"')
            .replace("”", '"')
    )

    # Remove extra spaces (but keep line breaks)
    text = re.sub(r"[ \t]+", " ", text)

    # Optionally lowercase all lyrics (helps sentiment analysis & embedding)
    if TO_LOWER:
        text = text.lower()

    return text.strip()


# ============ 3. Read CSV, batch-clean, and save ============

print(f"Reading CSV: {INPUT_CSV_PATH}")
df = pd.read_csv(INPUT_CSV_PATH)

if "lyrics" not in df.columns:
    raise ValueError("The current CSV does not contain the 'lyrics' column. Please check file column names.")

# Create new column: clean_lyrics
df["clean_lyrics"] = df["lyrics"].apply(clean_lyrics_one_song)

# Optionally keep only required columns for future processing:
df = df[["track_name", "artist_name", "play_count", "clean_lyrics"]]

df.to_csv(OUTPUT_CSV_PATH, index=False)
print(f"Cleaned CSV saved to: {OUTPUT_CSV_PATH}")
print(df[["track_name", "artist_name", "clean_lyrics"]].head())
