from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import os

import pandas as pd
from transformers import pipeline as hf_pipeline


def get_project_root() -> str:
    """Return the project root directory (parent of this file's package).

    This duplicates the logic in pipeline.get_project_root but avoids
    importing pipeline here, which caused a circular import.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


EMOTION_LABELS = ["happy", "sad", "angry", "relaxed", "energetic"]


@dataclass
class TrackWithLyrics:
    track_name: str
    artist_name: str
    clean_lyrics: str
    emotion: str | None = None


def _load_recent_cleaned_csv() -> pd.DataFrame:
    root = get_project_root()
    path = os.path.join(root, "realtime_data", "recent_tracks_cleaned.csv")
    if not os.path.exists(path):
        raise FileNotFoundError("recent_tracks_cleaned.csv not found. Please run /recent first.")
    df = pd.read_csv(path)
    # standardize columns
    col_map = {}
    if "track_name" in df.columns:
        col_map["track_name"] = "track_name"
    elif "title" in df.columns:
        col_map["title"] = "track_name"
    if "artist_name" in df.columns:
        col_map["artist_name"] = "artist_name"
    elif "artist" in df.columns:
        col_map["artist"] = "artist_name"
    if "clean_lyrics" in df.columns:
        col_map["clean_lyrics"] = "clean_lyrics"
    df = df.rename(columns=col_map)
    required = ["track_name", "artist_name", "clean_lyrics"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Column {c} missing from recent_tracks_cleaned.csv")
    df = df.dropna(subset=["clean_lyrics"])  # remove rows without lyrics
    return df


_mood_classifier = None


def _get_hf_classifier():
    global _mood_classifier
    if _mood_classifier is None:
        # use a lightweight multilabel emotion model from Hugging Face
        _mood_classifier = hf_pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)
    return _mood_classifier


def predict_emotion_for_recent_tracks() -> List[TrackWithLyrics]:
    df = _load_recent_cleaned_csv()
    clf = _get_hf_classifier()
    texts = df["clean_lyrics"].astype(str).tolist()
    results = clf(texts, truncation=True)
    emotions: List[str] = []
    for res in results:
        # res is list[{'label': 'joy', 'score': ...}, ...]
        best = max(res, key=lambda x: x["score"])
        label = str(best["label"]).lower()
        # map base emotions to our five categories
        if label in {"joy", "optimism", "love"}:
            emotions.append("happy")
        elif label in {"sadness", "grief"}:
            emotions.append("sad")
        elif label in {"anger"}:
            emotions.append("angry")
        elif label in {"disgust", "fear"}:
            emotions.append("energetic")
        else:
            emotions.append("relaxed")
    df["emotion"] = emotions
    tracks: List[TrackWithLyrics] = []
    for _, row in df.iterrows():
        tracks.append(
            TrackWithLyrics(
                track_name=str(row["track_name"]),
                artist_name=str(row["artist_name"]),
                clean_lyrics=str(row["clean_lyrics"]),
                emotion=str(row["emotion"]),
            )
        )
    return tracks


def infer_overall_emotion(tracks: List[TrackWithLyrics]) -> str:
    counts: Dict[str, int] = {}
    for t in tracks:
        if not t.emotion:
            continue
        counts[t.emotion] = counts.get(t.emotion, 0) + 1
    if not counts:
        return "unknown"
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _load_labeled_library() -> pd.DataFrame:
    root = get_project_root()
    path = os.path.join(root, "data", "tracks_with_emotionLabels.csv")
    if not os.path.exists(path):
        raise FileNotFoundError("tracks_with_emotionLabels.csv not found under data/")
    df = pd.read_csv(path)
    col_map: Dict[str, str] = {}
    # standardize basic columns
    if "track_name" in df.columns:
        col_map["track_name"] = "track_name"
    elif "title" in df.columns:
        col_map["title"] = "track_name"
    if "artist_name" in df.columns:
        col_map["artist_name"] = "artist_name"
    elif "artist" in df.columns:
        col_map["artist"] = "artist_name"

    # emotion column: your CSV uses true_emotion
    if "emotion" in df.columns:
        col_map["emotion"] = "emotion"
    elif "pred_emotion" in df.columns:
        col_map["pred_emotion"] = "emotion"
    elif "true_emotion" in df.columns:
        col_map["true_emotion"] = "emotion"

    df = df.rename(columns=col_map)

    required = ["track_name", "artist_name", "emotion"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Column {c} missing from tracks_with_emotionLabels.csv")

    # normalize emotion values to lower-case so that matching is robust
    df["emotion"] = df["emotion"].astype(str).str.lower()
    return df


def recommend_songs_by_overall_emotion(
    overall_emotion: str,
    existing_tracks: List[TrackWithLyrics],
    k: int = 10,
) -> List[Dict[str, Any]]:
    df = _load_labeled_library()

    # overall_emotion comes from our 5-category mapping; ensure comparable
    target = (overall_emotion or "").lower()

    existing_keys = {f"{t.track_name}::{t.artist_name}" for t in existing_tracks}

    # filter same emotion first (case-insensitive)
    same = df[df["emotion"].str.lower() == target].copy()
    if same.empty:
        candidates = df
    else:
        candidates = same

    candidates["_key"] = candidates["track_name"].astype(str) + "::" + candidates["artist_name"].astype(str)
    candidates = candidates[~candidates["_key"].isin(existing_keys)]

    if len(candidates) <= k:
        sampled = candidates
    else:
        sampled = candidates.sample(n=k, random_state=42)

    recs: List[Dict[str, Any]] = []
    for _, row in sampled.iterrows():
        recs.append(
            {
                "track_name": str(row["track_name"]),
                "artist_name": str(row["artist_name"]),
                "emotion": str(row["emotion"]),
            }
        )
    return recs
