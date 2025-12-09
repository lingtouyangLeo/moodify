import os
import requests
import urllib.parse
from typing import Dict, Any, List

CLIENT_ID = "b1afb850862a4e009d4fb92c9afed3b7"
CLIENT_SECRET = "c225b9248b18400ead7b085fbab985f4"
REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPE = "user-read-recently-played playlist-modify-public playlist-modify-private"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"


def build_auth_url() -> str:
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "show_dialog": "true",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str) -> Dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=data)
    r.raise_for_status()
    return r.json()


def fetch_recently_played(access_token: str, limit: int = 20) -> List[Dict[str, Any]]:
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": limit}
    r = requests.get(f"{API_BASE_URL}/me/player/recently-played", headers=headers, params=params)

    # print("DEBUG status:", r.status_code, "body:", r.text)
    r.raise_for_status()
    items = r.json().get("items", [])

    recent_list = []
    for item in items:
        track = item["track"]
        track_name = track["name"]
        artist_name = ", ".join([a["name"] for a in track["artists"]])
        recent_list.append({"track_name": track_name, "artist_name": artist_name})
    return recent_list

