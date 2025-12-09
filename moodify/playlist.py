import time
from typing import List, Dict, Any, Tuple

import requests

from .spotify import API_BASE_URL


def _auth_headers(access_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


def _get_current_user(access_token: str) -> Tuple[Dict[str, Any] | None, str | None]:
    try:
        r = requests.get(f"{API_BASE_URL}/me", headers=_auth_headers(access_token))
        if r.status_code != 200:
            return None, f"获取当前用户失败: {r.status_code} {r.text}"
        return r.json(), None
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def _create_playlist(access_token: str, user_id: str, name: str, description: str, public: bool = False) -> Tuple[Dict[str, Any] | None, str | None]:
    payload = {
        "name": name,
        "description": description,
        "public": public,
    }
    try:
        r = requests.post(f"{API_BASE_URL}/users/{user_id}/playlists", headers=_auth_headers(access_token), json=payload)
        if r.status_code not in (200, 201):
            return None, f"创建歌单失败: {r.status_code} {r.text}"
        return r.json(), None
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def _search_track(access_token: str, title: str, artist: str | None = None) -> Tuple[str | None, str | None]:
    if artist:
        q = f'track:"{title}" artist:"{artist}"'
    else:
        q = f'track:"{title}"'

    params = {"q": q, "type": "track", "limit": 1}
    try:
        r = requests.get(f"{API_BASE_URL}/search", headers=_auth_headers(access_token), params=params)
        if r.status_code != 200:
            return None, f"搜索失败: {r.status_code} {r.text}"
        items = r.json().get("tracks", {}).get("items", [])
        if not items:
            return None, "未找到匹配歌曲"
        return items[0]["id"], None
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def _add_tracks_to_playlist(access_token: str, playlist_id: str, track_ids: List[str]) -> str | None:
    if not track_ids:
        return None

    uris = [f"spotify:track:{tid}" for tid in track_ids]
    batch_size = 100
    try:
        for i in range(0, len(uris), batch_size):
            batch = uris[i : i + batch_size]
            payload = {"uris": batch}
            r = requests.post(f"{API_BASE_URL}/playlists/{playlist_id}/tracks", headers=_auth_headers(access_token), json=payload)
            if r.status_code not in (200, 201):
                return f"添加歌曲失败: {r.status_code} {r.text}"
            time.sleep(0.1)
        return None
    except Exception as exc:  # pragma: no cover
        return str(exc)


def create_playlist_from_recent(
    access_token: str,
    recent_tracks: List[Dict[str, Any]],
    playlist_name: str = "Imported Recent Tracks",
    playlist_description: str = "Imported from recent tracks via Moodify",
) -> Dict[str, Any]:
    """根据最近播放列表创建 Spotify 歌单并导入歌曲。

    返回结构示例：
    {
      "success": True/False,
      "playlist_id": str | None,
      "playlist_url": str | None,
      "added_count": int,
      "not_found": [{"track_name": ..., "artist_name": ..., "reason": ...}, ...],
      "error": str | None,
    }
    """

    user, err = _get_current_user(access_token)
    if err or not user:
        return {"success": False, "error": err or "无法获取当前用户"}

    playlist, err = _create_playlist(access_token, user["id"], playlist_name, playlist_description, public=False)
    if err or not playlist:
        return {"success": False, "error": err or "创建歌单失败"}

    playlist_id = playlist["id"]
    playlist_url = playlist.get("external_urls", {}).get("spotify")

    track_ids: List[str] = []
    not_found: List[Dict[str, str]] = []

    for item in recent_tracks:
        title = (item.get("track_name") or "").strip()
        artist = (item.get("artist_name") or "").strip()
        if not title:
            continue
        track_id, terr = _search_track(access_token, title, artist)
        if track_id:
            track_ids.append(track_id)
        else:
            not_found.append({"track_name": title, "artist_name": artist, "reason": terr or "未找到匹配"})
        time.sleep(0.1)

    add_err = _add_tracks_to_playlist(access_token, playlist_id, track_ids)
    if add_err:
        return {
            "success": False,
            "playlist_id": playlist_id,
            "playlist_url": playlist_url,
            "added_count": len(track_ids),
            "not_found": not_found,
            "error": add_err,
        }

    return {
        "success": True,
        "playlist_id": playlist_id,
        "playlist_url": playlist_url,
        "added_count": len(track_ids),
        "not_found": not_found,
        "error": None,
    }

