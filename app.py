from flask import Flask, redirect, request, url_for, session
import os

from moodify import spotify, lyrics, storage, playlist

app = Flask(__name__)

app.secret_key = "replace_with_your_own_secret_key"

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
    return redirect(url_for("recent_tracks"))


@app.route("/recent")
def recent_tracks():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    try:
        recent_list = spotify.fetch_recently_played(access_token, limit=20)
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

    # Cache recent tracks in session for playlist import
    session["recent_list"] = recent_list

    # Save to top-level realtime_data/ folder
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, "realtime_data")
    os.makedirs(data_dir, exist_ok=True)
    filepath = storage.save_recent_list(data_dir, recent_list)

    processed_tracks = lyrics.process_recent_tracks(recent_list)
    saved = storage.save_processed_tracks(data_dir, processed_tracks)

    html = BASE_HTML_START
    html += "<h1>Your 20 Most Recent Tracks</h1>"
    html += "<p class='tagline'>We fetched your latest listening history, attached lyrics, and saved everything for analysis.</p>"

    html += "<div class='section'>"
    html += "<div class='section-header'>Generated Files</div>"
    html += "<ul class='file-list'>"
    html += f"<li><strong>Raw list</strong>: {os.path.basename(filepath)}</li>"
    html += f"<li><strong>With lyrics</strong>: {os.path.basename(saved['lyrics_json'])}</li>"
    html += f"<li><strong>Cleaned lyrics CSV</strong>: {os.path.basename(saved['cleaned_csv'])}</li>"
    html += "</ul>"
    html += "</div>"

    if lyrics.genius_client is None:
        html += "<div class='note-warning'>Note: <code>GENIUS_ACCESS_TOKEN</code> is not configured, so lyrics fetching is currently disabled.</div>"

    html += "<div class='section'>"
    html += "<div class='section-header'>Recently Played Tracks</div>"
    html += "<ul class='track-list'>"
    for t in processed_tracks:
        status_badge = (
            "<span class='badge-ok'>Lyrics OK</span>"
            if t.get("clean_lyrics")
            else f"<span class='badge-failed'>Lyrics failed</span>"
        )
        error_text = ""
        if not t.get("clean_lyrics") and t.get("error"):
            error_text = f" &mdash; <span style='color:#ff7675;font-size:12px;'>({t.get('error')})</span>"
        html += (
            f"<li><strong>{t.get('track_name')}</strong> &middot; {t.get('artist_name')} "
            f"{status_badge}{error_text}</li>"
        )
    html += "</ul>"
    html += "</div>"

    # Form to import into a Spotify playlist
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

    html += "<div class='footer-links'><a href='/'>Back to Home</a></div>"

    html += BASE_HTML_END

    return html


@app.route("/import_playlist", methods=["POST"])
def import_playlist():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("index"))

    recent_list = session.get("recent_list")
    if not recent_list:
        # Fallback: try to load from realtime_data/recent_tracks.json
        base_dir = os.path.dirname(__file__)
        json_path = os.path.join(base_dir, "realtime_data", "recent_tracks.json")
        if os.path.exists(json_path):
            import json

            with open(json_path, "r", encoding="utf-8") as f:
                recent_list = json.load(f)
        else:
            return (
                BASE_HTML_START
                + """
                <h1>No recent tracks found</h1>
                <p class='note-warning'>No recent tracks found for this session. Please visit <code>/recent</code> first to fetch them.</p>
                <div class='footer-links'><a href='/'>Back to Home</a></div>
                """
                + BASE_HTML_END
            )

    playlist_name = request.form.get("playlist_name") or "Imported Recent Tracks"
    description = request.form.get("description") or "Imported from recent tracks via Moodify"

    result = playlist.create_playlist_from_recent(access_token, recent_list, playlist_name, description)

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


if __name__ == "__main__":
    app.run(debug=True)