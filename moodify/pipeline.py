import json
import os
from typing import Any, Dict, List

from . import spotify, lyrics, storage, playlist
from . import mood


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


def create_mood_playlist_pipeline(
    access_token: str,
    playlist_name: str | None = None,
    description: str | None = None,
    base_dir: str | None = None,
) -> Dict[str, Any]:
    """Run mood analysis on recent_tracks_cleaned.csv and create a mood-based recommendation playlist.

    This pipeline does **not** refetch recent tracks. It assumes
    realtime_data/recent_tracks_cleaned.csv already exists.
    """

    try:
        tracks_with_emotion = mood.predict_emotion_for_recent_tracks()
        overall_emotion = mood.infer_overall_emotion(tracks_with_emotion)

        recommended_tracks = mood.recommend_songs_by_overall_emotion(
            overall_emotion,
            existing_tracks=tracks_with_emotion,
            k=10,
        )

        final_playlist_name = playlist_name or f"Moodify: {overall_emotion.title()} Picks"
        final_description = description or f"10 songs recommended based on the {overall_emotion} mood of my recent tracks via Moodify."

        playlist_result = playlist.create_playlist_from_recommendations(
            access_token,
            recommended_tracks,
            playlist_name=final_playlist_name,
            playlist_description=final_description,
        )

        return {
            "success": bool(playlist_result.get("success")),
            "overall_emotion": overall_emotion,
            "tracks_with_emotion": [t.__dict__ for t in tracks_with_emotion],
            "recommended_tracks": recommended_tracks,
            "playlist_id": playlist_result.get("playlist_id"),
            "playlist_url": playlist_result.get("playlist_url"),
            "added_count": playlist_result.get("added_count", 0),
            "not_found": playlist_result.get("not_found", []),
            "error": playlist_result.get("error"),
        }
    except Exception as exc:
        return {
            "success": False,
            "overall_emotion": None,
            "tracks_with_emotion": None,
            "recommended_tracks": None,
            "playlist_id": None,
            "playlist_url": None,
            "added_count": 0,
            "not_found": [],
            "error": str(exc),
        }
