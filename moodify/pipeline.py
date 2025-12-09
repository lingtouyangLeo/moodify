import json
import os
from typing import Any, Dict, List

from . import spotify, lyrics, storage, playlist


def get_project_root() -> str:
    """Return the project root directory (parent of this file's package).

    This is used to locate the top-level realtime_data/ folder.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def get_realtime_data_dir(base_dir: str | None = None) -> str:
    """Return the realtime_data directory under the given base directory.

    If base_dir is None, project root is used.
    """
    if base_dir is None:
        base_dir = get_project_root()
    data_dir = os.path.join(base_dir, "realtime_data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def run_recent_tracks_pipeline(access_token: str, limit: int = 20, base_dir: str | None = None) -> Dict[str, Any]:
    """End-to-end pipeline: fetch recent tracks, attach & clean lyrics, save to realtime_data.

    Returns a dictionary containing:
      - recent_list: the raw recent track dicts
      - processed_tracks: track dicts with lyrics/clean_lyrics/error
      - files: paths of saved JSON/CSV files
      - lyrics_enabled: whether Genius client is configured
    """
    recent_list = spotify.fetch_recently_played(access_token, limit=limit)
    processed_tracks = lyrics.process_recent_tracks(recent_list)

    data_dir = get_realtime_data_dir(base_dir)
    raw_path = storage.save_recent_list(data_dir, recent_list)
    saved_paths = storage.save_processed_tracks(data_dir, processed_tracks)

    return {
        "recent_list": recent_list,
        "processed_tracks": processed_tracks,
        "files": {
            "raw": raw_path,
            **saved_paths,
        },
        "lyrics_enabled": lyrics.genius_client is not None,
    }


def create_playlist_pipeline(
    access_token: str,
    playlist_name: str,
    description: str,
    recent_list: List[Dict[str, Any]] | None = None,
    base_dir: str | None = None,
) -> Dict[str, Any]:
    """Create a Spotify playlist from recent tracks.

    If recent_list is None, this function attempts to load it from
    realtime_data/recent_tracks.json under the computed base_dir.
    """
    if recent_list is None:
        data_dir = get_realtime_data_dir(base_dir)
        json_path = os.path.join(data_dir, "recent_tracks.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                recent_list = json.load(f)
        else:
            return {
                "success": False,
                "error": "No recent_tracks.json found in realtime_data. Please visit /recent first.",
            }

    return playlist.create_playlist_from_recent(
        access_token,
        recent_list,
        playlist_name=playlist_name,
        playlist_description=description,
    )


