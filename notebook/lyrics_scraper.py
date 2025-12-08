import os
import json
import time
import random
import pandas as pd
import lyricsgenius
from tqdm import tqdm

# ========== 0. Basic Configuration ==========
client_access_token = "3AhYPPIL5RQbybxGO0UvFk2OH_ZHkiN6w07CVwy9WNrLzxN0qhBDW2rIRkV8041e"  # ⚠️ Replace with your own token

genius = lyricsgenius.Genius(
    client_access_token,
    timeout=15,
    skip_non_songs=True,
    remove_section_headers=True,
)

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
input_json_path = os.path.join(PROJECT_ROOT, "data", "top1000HitSongs.json")
output_csv_path = os.path.join(PROJECT_ROOT, "data", "tracks_with_lyrics.csv")

# Save intermediate results every N songs
CHECKPOINT_EVERY = 100

# If you want to test, limit the number; set to None to process all
MAX_SONGS = None  # For example, set 500 if you only want to run 500 songs

# ========== 1. Read JSON (one song per line) ==========
tracks = []
with open(input_json_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        tracks.append(data)

print(f"Read {len(tracks)} songs from JSON")

# ========== 2. Load existing CSV for checkpointing + avoiding repeated failures ==========
results = []  # Used to store all results (current run + history)
processed_keys = set()        # All processed (track_name, artist_name)
processed_success = set()     # Keys that successfully retrieved lyrics
processed_error = set()       # Keys that had an error

if os.path.exists(output_csv_path):
    print(f"Detected existing file: {output_csv_path}, attempting to resume crawling...")
    df_existing = pd.read_csv(output_csv_path)

    # Put existing records into results; later we will append new ones
    results = df_existing.to_dict(orient="records")

    for _, row in df_existing.iterrows():
        track_name_old = str(row.get("track_name", ""))
        artist_name_old = str(row.get("artist_name", ""))
        key = (track_name_old, artist_name_old)

        processed_keys.add(key)

        lyrics_old = row.get("lyrics")
        error_old = row.get("error")

        # Has lyrics → success
        if isinstance(lyrics_old, str) and lyrics_old.strip() != "":
            processed_success.add(key)
        # No lyrics but has error → considered failed
        elif isinstance(error_old, str) and error_old.strip() != "":
            processed_error.add(key)

    print(f"Existing records: {len(results)}")
    print(f"Success: {len(processed_success)}, Failed: {len(processed_error)}")
else:
    print("No existing CSV detected. Starting from scratch.")

# Current number of results (used for checkpoint calculation)
current_count = len(results)

# ========== 3. Main Loop: fetch lyrics + auto skip + intermediate save ==========
new_fetched = 0  # Count of newly fetched songs in this run

for i, item in enumerate(tqdm(tracks, desc="Fetching lyrics")):
    # If MAX_SONGS is set, limit total processed amount (including history)
    if MAX_SONGS is not None and (new_fetched + len(processed_keys)) >= MAX_SONGS:
        break

    track_name = item.get("track_name")
    artist_name = item.get("artist_name")
    play_count = item.get("play_count")

    key = (str(track_name), str(artist_name))

    # 1) Auto-skip songs already processed (whether success or failure)
    if key in processed_keys:
        # If you want to retry failed songs, modify logic here
        continue

    lyrics = None
    error_msg = None

    try:
        song = genius.search_song(track_name, artist_name)
        if song is not None and isinstance(song.lyrics, str) and song.lyrics.strip() != "":
            lyrics = song.lyrics
        else:
            error_msg = "Song not found or empty lyrics"
    except Exception as e:
        error_msg = str(e)

    results.append({
        "track_name": track_name,
        "artist_name": artist_name,
        "play_count": play_count,
        "lyrics": lyrics,
        "error": error_msg,
    })

    # Update state sets
    processed_keys.add(key)
    if lyrics is not None and lyrics.strip() != "":
        processed_success.add(key)
    else:
        processed_error.add(key)

    new_fetched += 1
    current_count += 1

    # 2) Auto-save every 100 songs
    if current_count % CHECKPOINT_EVERY == 0:
        df_checkpoint = pd.DataFrame(results)
        df_checkpoint.to_csv(output_csv_path, index=False)
        print(f"\nCheckpoint saved: {current_count} records (including history + current run)")

    # 3) Random sleep 3–6 seconds to avoid rate limits
    time.sleep(random.uniform(3, 6))

# ========== 4. Final save ==========
df_final = pd.DataFrame(results)
df_final.to_csv(output_csv_path, index=False)
print(f"\nAll done! Final total saved: {len(results)} records (including history + current run).")
print(f"File path: {output_csv_path}")
