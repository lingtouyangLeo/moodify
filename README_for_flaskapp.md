# Moodify Flask App Guide

This document explains how to configure the `.env` environment file for this project and how to run the Flask application locally.

---

## 1. Configure the `.env` file

This project uses environment variables to store all sensitive information (Spotify/Genius API keys, Flask secret key, etc.). These variables are loaded from a `.env` file in the project root.

### 1.1 Create `.env` in the project root

In the repository root (the same directory as `app.py`), create a file named `.env` with contents similar to:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback

GENIUS_ACCESS_TOKEN=your_genius_access_token

FLASK_SECRET_KEY=a_random_long_string_for_flask_session_encryption
```

You can obtain these credentials from the official developer portals:

- Spotify Developer Dashboard: https://developer.spotify.com/
- Genius API Clients: https://genius.com/api-clients

Notes:

- **Do not** commit `.env` to the Git repository (this project’s `.gitignore` already ignores it).
- `SPOTIFY_REDIRECT_URI` must exactly match the Redirect URI configured in the Spotify Developer Dashboard (including host, port, and path).
- Use `KEY=value` format for all entries; quotes are generally not required.

When Flask starts, it loads the environment variables from `.env` in `app.py` via:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 2. Install dependencies

Make sure you are using a suitable Python environment (for example, Python 3.10+/3.11/3.12). It is recommended to create a virtual environment first:

```bash
cd /path/to/moodify

python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt` includes all external libraries used by this project, such as Flask, Requests, Pandas, Transformers, Torch, lyricsgenius, and langdetect.

---

## 3. Run the Flask app

From the project root (the directory that contains `app.py`), run:

```bash
cd /path/to/moodify

# If the virtual environment is not activated yet, activate it first
source .venv/bin/activate  # On Windows use .venv\Scripts\activate

python app.py
```

If startup is successful, the terminal will show something like:

```text
* Serving Flask app 'app'
* Debug mode: on
* Running on http://127.0.0.1:5000
```

In your browser, open:

- Home: `http://127.0.0.1:5000/`

### 3.1 Usage flow

1. Open the home page and click **“Log in with Spotify”**, then follow the prompts to authorize in Spotify.
2. After authorization, you will be redirected to a page that shows “Spotify authorization successful” and a button:
   - **“Fetch and process my recent tracks”**
   - Clicking this button will call the Spotify API to fetch your recently played tracks, attempt to fetch and clean lyrics, and save the results into the `realtime_data/` folder at the project root (as JSON and CSV files).
3. When processing is complete, you will be redirected to the `/recent` page:
   - Shows the generated files (raw recent tracks JSON, with-lyrics JSON, cleaned lyrics CSV);
   - Displays the list of your 20 most recent tracks;
   - Provides form buttons to:
     - Create a Spotify playlist based on your recent tracks;
     - Analyze the mood of the lyrics, recommend 10 tracks with a similar emotion from the labeled library, and create a new playlist;
     - **“Refresh recent data from Spotify”**: if you have listened to more music, click this button to fetch your latest recently played tracks again and update `realtime_data/`.

### 3.2 Stop the server

Press `Ctrl + C` in the terminal to stop the Flask development server.

---

## 4. Deployment and security notes

- **Never** upload `.env` to GitHub or any other public repository.
- For any Spotify/Genius credentials that have already been exposed, it is recommended to reset them (Regenerate / Revoke) in their respective Developer Dashboards and update the values in `.env`.
- The current startup method (`python app.py`) uses Flask’s built-in development server and is suitable only for local development and testing. For production deployment, use a production-grade WSGI server (such as gunicorn or uWSGI) and configure the same environment variables in the deployment environment.
