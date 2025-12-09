from flask import Flask, redirect, request, url_for, session
import os
from dotenv import load_dotenv
load_dotenv()
# CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
# CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
# REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
# print("DEBUG SPOTIFY_CLIENT_ID:", CLIENT_ID)
# print("DEBUG SPOTIFY_REDIRECT_URI:", REDIRECT_URI)

from moodify import spotify
from moodify import pipeline

app = Flask(__name__)

# app.secret_key = "replace_with_your_own_secret_key"
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")


BASE_HTML_START = """<!DOCTYPE html>
<html lang='en'>
  <head>
    <meta charset='utf-8'>
    <title>Spotify Recent Tracks Demo</title>
    <style>
      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        padding: 0;
        background: #0b1020;
        color: #f5f5f5;
      }
      .page {
        max-width: 900px;
        margin: 40px auto;
        padding: 32px 28px 40px;
        background: #151b2f;
        border-radius: 18px;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
      }
      h1 {
        margin-top: 0;
        font-size: 28px;
        letter-spacing: 0.03em;
      }
      h3 {
        margin-top: 28px;
        font-size: 20px;
      }
      p {
        line-height: 1.6;
      }
      a.button, button.primary {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 999px;
        border: none;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-decoration: none;
        cursor: pointer;
        transition: transform 0.08s ease, box-shadow 0.08s ease, background 0.12s ease;
      }
      a.button.primary, button.primary {
        background: #1db954;
        color: #0b1020;
        box-shadow: 0 8px 18px rgba(29, 185, 84, 0.4);
      }
      a.button.primary:hover, button.primary:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(29, 185, 84, 0.5);
      }
      a.button.secondary {
        margin-top: 6px;
        background: transparent;
        color: #9ba3c7;
        border: 1px solid #2e3550;
      }
      a.button.secondary:hover {
        background: #20263d;
      }
      .tagline {
        color: #9ba3c7;
        margin-bottom: 24px;
      }
      .section {
        margin-top: 24px;
        padding-top: 12px;
        border-top: 1px solid #222842;
      }
      .section-header {
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #8a92b4;
        margin-bottom: 10px;
      }
      .file-list, .track-list, .not-found-list {
        list-style: none;
        padding-left: 0;
        margin-top: 6px;
      }
      .file-list li, .track-list li, .not-found-list li {
        padding: 6px 0;
        border-bottom: 1px solid #222842;
        font-size: 14px;
      }
      .file-list li:last-child,
      .track-list li:last-child,
      .not-found-list li:last-child {
        border-bottom: none;
      }
      .badge-ok {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background: rgba(46, 213, 115, 0.12);
        color: #2ed573;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-left: 8px;
      }
      .badge-failed {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background: rgba(255, 71, 87, 0.12);
        color: #ff4757;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-left: 8px;
      }
      .note-warning {
        margin-top: 10px;
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(255, 193, 7, 0.08);
        border: 1px solid rgba(255, 193, 7, 0.4);
        color: #ffeaa7;
        font-size: 13px;
      }
      .note-error {
        margin-top: 10px;
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(255, 71, 87, 0.12);
        border: 1px solid rgba(255, 71, 87, 0.6);
        color: #ff7675;
        font-size: 13px;
      }
      form label {
        display: block;
        font-size: 13px;
        color: #9ba3c7;
        margin-top: 12px;
        margin-bottom: 4px;
      }
      input[type='text'] {
        width: 100%;
        max-width: 420px;
        padding: 8px 10px;
        border-radius: 8px;
        border: 1px solid #2e3550;
        background: #0f1424;
        color: #f5f5f5;
        font-size: 14px;
      }
      input[type='text']:focus {
        outline: none;
        border-color: #1db954;
        box-shadow: 0 0 0 1px rgba(29, 185, 84, 0.35);
      }
      .spacer-sm {
        height: 8px;
      }
      .spacer-md {
        height: 16px;
      }
      .footer-links {
        margin-top: 22px;
        font-size: 13px;
      }
      .footer-links a {
        color: #9ba3c7;
        text-decoration: none;
      }
      .footer-links a:hover {
        text-decoration: underline;
      }
    </style>
  </head>
  <body>
    <div class='page'>
"""

BASE_HTML_END = """
    </div>
  </body>
</html>
"""


@app.route("/")
def index():
    return (
        BASE_HTML_START
        + """
        <h1>Spotify Recent Tracks Demo</h1>
        <p class='tagline'>Log in with Spotify, capture your latest listening session, clean the lyrics, and spin up a playlist in one click.</p>

        <a href="/login" class="button primary">Log in with Spotify</a>

        <div class="footer-links">
          <span>Once logged in, you will be redirected automatically to your recent tracks view.</span>
        </div>
        """
        + BASE_HTML_END
    )


@app.route("/login")
def login():
    return redirect(spotify.build_auth_url())


@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return (
            BASE_HTML_START
            + """
            <h1>Authorization failed</h1>
            <p class='note-error'>Missing <code>code</code> parameter from Spotify callback.</p>
            <div class='footer-links'><a href='/'>Back to Home</a></div>
            """
            + BASE_HTML_END
        )

    token_json = spotify.exchange_code_for_token(code)
    session["access_token"] = token_json["access_token"]

    # Show a page with an explicit button to fetch and process recent tracks.
    html = BASE_HTML_START
    html += "<h1>Spotify authorization successful</h1>"
    html += "<p class='tagline'>You're now connected to Spotify. Click the button below to fetch your recent tracks, attach lyrics, and save them for analysis.</p>"
    html += "<form method='post' action='/fetch_recent'>"
    html += "<button type='submit' class='primary'>Fetch and process my recent tracks</button>"
    html += "</form>"
    html += "<div class='footer-links'><a href='/'>Back to Home</a></div>"
    html += BASE_HTML_END
    return html


@app.route("/fetch_recent", methods=["POST"])
def fetch_recent():
    """Explicit action to run the recent-tracks pipeline once and save to realtime_data.

    After this, /recent will read from files under realtime_data/.
    """
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    try:
        # Run pipeline just to generate realtime_data files; we ignore the
        # in-memory result here and always render /recent from disk.
        pipeline.run_recent_tracks_pipeline(access_token, limit=20)
    except Exception as exc:
        return (
            BASE_HTML_START
            + f"""
            <h1>Failed to fetch tracks</h1>
            <p class='note-error'>Failed to fetch recently played tracks: {str(exc)}</p>
            <div class='footer-links'><a href='/'>Back to Home</a></div>
            """
            + BASE_HTML_END
        )

    return redirect(url_for("recent_tracks"))


@app.route("/recent")
def recent_tracks():
    """Render recent tracks by reading data from realtime_data on disk.

    This view no longer calls Spotify or the pipeline directly. It expects
    that /fetch_recent has been run at least once in this session, which
    populates realtime_data/recent_tracks.json and the processed files.
    """
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    # Read files from realtime_data directory.
    from moodify import storage  # local import to avoid circulars

    base_dir = pipeline.get_realtime_data_dir()
    raw_json_path = os.path.join(base_dir, "recent_tracks.json")
    lyrics_json_path = os.path.join(base_dir, "recent_tracks_with_lyrics.json")
    cleaned_csv_path = os.path.join(base_dir, "recent_tracks_cleaned.csv")

    if not os.path.exists(raw_json_path):
        # User hasn't clicked fetch yet.
        html = BASE_HTML_START
        html += "<h1>No recent tracks data found</h1>"
        html += "<p class='note-warning'>You haven't fetched your recent tracks yet. Please go back and click the fetch button after authorizing Spotify.</p>"
        html += "<div class='footer-links'><a href='/callback'>Back to authorization result</a></div>"
        html += BASE_HTML_END
        return html

    # Load the raw recent list from JSON
    import json

    with open(raw_json_path, "r", encoding="utf-8") as f:
        recent_list = json.load(f)

    # Load processed tracks (with lyrics / clean_lyrics) if available
    processed_tracks = storage.load_processed_tracks(base_dir) if hasattr(storage, "load_processed_tracks") else []

    html = BASE_HTML_START
    html += "<h1>Your 20 Most Recent Tracks</h1>"
    html += "<p class='tagline'>We fetched your latest listening history, attached lyrics, and saved everything for analysis.</p>"

    # Files section
    html += "<div class='section'>"
    html += "<div class='section-header'>Generated Files</div>"
    html += "<ul class='file-list'>"
    html += f"<li><strong>Raw list</strong>: {os.path.basename(raw_json_path)}</li>"
    if os.path.exists(lyrics_json_path):
        html += f"<li><strong>With lyrics</strong>: {os.path.basename(lyrics_json_path)}</li>"
    if os.path.exists(cleaned_csv_path):
        html += f"<li><strong>Cleaned lyrics CSV</strong>: {os.path.basename(cleaned_csv_path)}</li>"
    html += "</ul>"
    html += "</div>"

    # Recently played tracks section (prefer processed_tracks if available)
    html += "<div class='section'>"
    html += "<div class='section-header'>Recently Played Tracks</div>"
    html += "<ul class='track-list'>"
    tracks_for_display = processed_tracks or recent_list
    for t in tracks_for_display:
        title = t.get("track_name") or t.get("title") or ""
        artist = t.get("artist_name") or t.get("artist") or ""
        status_badge = (
            "<span class='badge-ok'>Lyrics OK</span>"
            if t.get("clean_lyrics")
            else ""
        )
        error_text = ""
        if not t.get("clean_lyrics") and t.get("error"):
            error_text = f" &mdash; <span style='color:#ff7675;font-size:12px;'>({t.get('error')})</span>"
        html += (
            f"<li><strong>{title}</strong> &middot; {artist} "
            f"{status_badge}{error_text}</li>"
        )
    html += "</ul>"
    html += "</div>"

    # Create playlist form (from raw recent_list in memory)
    html += "<div class='section'>"
    html += "<div class='section-header'>Create Playlist</div>"
    html += "<p>Create a Spotify playlist from these recent tracks in one click.</p>"
    html += "<form method='post' action='/import_playlist'>"
    html += "<label for='playlist_name'>Playlist name</label>"
    html += "<input type='text' id='playlist_name' name='playlist_name' value='Imported Recent Tracks'>"
    html += "<label for='description'>Description</label>"
    html += "<input type='text' id='description' name='description' value='Imported from recent tracks via Moodify'>"
    html += "<div class='spacer-md'></div>"
    html += "<button type='submit' class='primary'>Import to Spotify Playlist</button>"
    html += "</form>"
    html += "</div>"

    # Mood-based recommendation section (works off realtime_data cleaned CSV)
    html += "<div class='section'>"
    html += "<div class='section-header'>Mood-based Recommendations</div>"
    html += "<p>Analyze the mood of your recent tracks, recommend 10 songs with a similar emotion from the labeled library, and create a new playlist.</p>"
    html += "<form method='post' action='/mood_recommend'>"
    html += "<label for='mood_playlist_name'>Playlist name</label>"
    html += "<input type='text' id='mood_playlist_name' name='playlist_name' value='Mood-based Recommendations from Recent'>"
    html += "<label for='mood_description'>Description</label>"
    html += "<input type='text' id='mood_description' name='description' value='Recommended based on the mood of my recent tracks via Moodify'>"
    html += "<div class='spacer-md'></div>"
    html += "<button type='submit' class='primary'>Create Mood-based Playlist</button>"
    html += "</form>"
    html += "</div>"

    # Refresh data section: allow user to re-run fetch_recent to update realtime_data
    html += "<div class='section'>"
    html += "<div class='section-header'>Refresh Recent Data</div>"
    html += "<p>If you've listened to more music and want to update this view, click below to fetch your latest recent tracks from Spotify again.</p>"
    html += "<form method='post' action='/fetch_recent'>"
    html += "<div class='spacer-md'></div>"
    html += "<button type='submit' class='primary'>Refresh recent data from Spotify</button>"
    html += "</form>"
    html += "</div>"

    html += "<div class='footer-links'><a href='/'>Back to Home</a></div>"

    html += BASE_HTML_END

    return html


@app.route("/import_playlist", methods=["POST"])
def import_playlist():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    # Load recent_list directly from realtime_data json
    base_dir = pipeline.get_realtime_data_dir()
    raw_json_path = os.path.join(base_dir, "recent_tracks.json")
    if not os.path.exists(raw_json_path):
        return redirect(url_for("recent_tracks"))
    import json

    with open(raw_json_path, "r", encoding="utf-8") as f:
        recent_list = json.load(f)

    playlist_name = request.form.get("playlist_name") or "Imported Recent Tracks"
    description = request.form.get("description") or "Imported from recent tracks via Moodify"

    result = pipeline.create_playlist_pipeline(
        access_token,
        playlist_name=playlist_name,
        description=description,
        recent_list=recent_list,
    )

    if not result.get("success"):
        error = result.get("error") or "Unknown error"
        html = BASE_HTML_START
        html += "<h1>Failed to import playlist</h1>"
        html += f"<p class='note-error'>Error while creating playlist or adding tracks: {error}</p>"
        html += "<div class='footer-links'><a href='/recent'>Back to Recent Tracks</a></div>"
        html += BASE_HTML_END
        return html

    html = BASE_HTML_START
    html += "<h1>Playlist imported successfully</h1>"
    html += f"<p class='tagline'>We created a new Spotify playlist from your recent tracks.</p>"
    html += f"<p>Created playlist: <strong>{playlist_name}</strong></p>"
    if result.get("playlist_url"):
        html += (
            f"<p>Open in Spotify: "
            f"<a href='{result['playlist_url']}' target='_blank' class='button secondary'>Open playlist</a></p>"
        )

    html += f"<p>Number of tracks added: <strong>{result.get('added_count', 0)}</strong></p>"

    not_found = result.get("not_found") or []
    if not_found:
        html += "<div class='section'>"
        html += "<div class='section-header'>Unmatched Tracks</div>"
        html += "<p>These tracks could not be matched on Spotify. You may want to search and add them manually:</p>"
        html += "<ul class='not-found-list'>"
        for item in not_found:
            html += (
                f"<li>{item.get('track_name')} &middot; {item.get('artist_name')} "
                f"<span style='color:#ff7675;font-size:12px;'>({item.get('reason')})</span></li>"
            )
        html += "</ul>"
        html += "</div>"

    html += "<div class='footer-links'><a href='/recent'>Back to Recent Tracks</a></div>"

    html += BASE_HTML_END

    return html


@app.route("/mood_recommend", methods=["POST"])
def mood_recommend():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    playlist_name = request.form.get("playlist_name") or "Mood-based Recommendations from Recent"
    description = request.form.get("description") or "Recommended based on the mood of my recent tracks via Moodify"

    result = pipeline.create_mood_playlist_pipeline(
        access_token,
        playlist_name=playlist_name,
        description=description,
    )

    if not result.get("success"):
        error = result.get("error") or "Unknown error"
        html = BASE_HTML_START
        html += "<h1>Failed to create mood-based playlist</h1>"
        html += f"<p class='note-error'>Error while creating mood-based recommendation playlist: {error}</p>"
        html += "<div class='footer-links'><a href='/recent'>Back to Recent Tracks</a></div>"
        html += BASE_HTML_END
        return html

    overall_emotion = result.get("overall_emotion") or "unknown"
    recommended_tracks = result.get("recommended_tracks") or []

    html = BASE_HTML_START
    html += "<h1>Mood-based playlist created</h1>"
    html += f"<p class='tagline'>We analyzed the mood of your recent tracks and detected an overall emotion: <strong>{overall_emotion}</strong>.</p>"

    if result.get("playlist_url"):
        html += (
            f"<p>Open the new playlist on Spotify: "
            f"<a href='{result['playlist_url']}' target='_blank' class='button secondary'>Open playlist</a></p>"
        )

    html += f"<p>Number of recommended tracks added: <strong>{result.get('added_count', 0)}</strong></p>"

    if recommended_tracks:
        html += "<div class='section'>"
        html += "<div class='section-header'>Recommended Tracks</div>"
        html += "<ul class='track-list'>"
        for t in recommended_tracks:
            html += (
                f"<li><strong>{t.get('track_name')}</strong> · {t.get('artist_name')} "
                f"<span style='color:#9ba3c7;font-size:12px;'>(emotion: {t.get('emotion')})</span></li>"
            )
        html += "</ul>"
        html += "</div>"

    not_found = result.get("not_found") or []
    if not_found:
        html += "<div class='section'>"
        html += "<div class='section-header'>Unmatched Tracks</div>"
        html += "<p>The following recommended songs could not be matched on Spotify:</p>"
        html += "<ul class='not-found-list'>"
        for item in not_found:
            html += (
                f"<li>{item.get('track_name')} · {item.get('artist_name')} "
                f"<span style='color:#ff7675;font-size:12px;'>({item.get('reason')})</span></li>"
            )
        html += "</ul>"
        html += "</div>"

    html += "<div class='footer-links'><a href='/recent'>Back to Recent Tracks</a></div>"

    html += BASE_HTML_END

    return html


if __name__ == "__main__":
    app.run(debug=True)

