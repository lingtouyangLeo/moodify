import os
import json
import csv
from typing import List, Dict, Any


def ensure_data_dir(base_dir: str) -> str:
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def save_recent_list(data_dir: str, recent_list: List[Dict[str, Any]]) -> str:
    filepath = os.path.join(data_dir, "recent_tracks.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(recent_list, f, ensure_ascii=False, indent=2)
    return filepath


def save_processed_tracks(data_dir: str, processed_tracks: List[Dict[str, Any]]) -> Dict[str, str]:
    lyrics_json_path = os.path.join(data_dir, "recent_tracks_with_lyrics.json")
    with open(lyrics_json_path, "w", encoding="utf-8") as f:
        json.dump(processed_tracks, f, ensure_ascii=False, indent=2)

    cleaned_csv_path = os.path.join(data_dir, "recent_tracks_cleaned.csv")
    with open(cleaned_csv_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["track_name", "artist_name", "clean_lyrics", "error"])
        for t in processed_tracks:
            writer.writerow([
                t.get("track_name", ""),
                t.get("artist_name", ""),
                t.get("clean_lyrics", ""),
                t.get("error", ""),
            ])

    return {"lyrics_json": lyrics_json_path, "cleaned_csv": cleaned_csv_path}

