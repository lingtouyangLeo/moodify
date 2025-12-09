# Moodify

An emotion-aware music recommendation system that analyzes song lyrics to classify tracks by emotional content and generate mood-based playlists.

## Table of Contents

- [Project Overview](#project-overview)
- [Web Application](#web-application)
- [Features](#features)
- [Dataset](#dataset)
- [Installation](#installation)
- [Code Execution Instructions](#code-execution-instructions)
- [High-Level Code Logic](#high-level-code-logic)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [License](#license)

## Project Overview

Moodify is a music recommendation system that leverages Natural Language Processing (NLP) to analyze song lyrics and classify tracks based on emotional content. The system processes data from the Spotify Million Playlist Dataset, extracts lyrics, and uses zero-shot classification models to assign emotional scores to each song. This enables mood-based playlist generation and emotion-aware music recommendations.

## Web Application

We've developed a web-based interface for Moodify using Flask, allowing users to interact with the emotion-aware music recommendation system through their browser. The web application provides an intuitive way to generate mood-based playlists and explore emotion-classified songs.

For detailed information about the web application, including setup instructions, API endpoints, and usage examples, please refer to the [Flask App README](README_for_flaskapp.md).

## Features

- **Data Processing**: Extract top 1000 hit songs from Spotify Million Playlist Dataset using PySpark
- **Lyrics Extraction**: Automated lyrics scraping from Genius API
- **Text Cleaning**: Comprehensive lyrics preprocessing and normalization
- **Emotion Analysis**: Multi-label emotion classification using Facebook's BART-large-MNLI model
- **Mood-Based Playlists**: Generate playlists based on five emotion categories: happy, sad, angry, relaxed, and energetic

## Dataset

The project uses the [Spotify Million Playlist Dataset](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge), which contains over 1 million playlists created by Spotify users. From this dataset, we extract the top 1000 most frequently played songs and analyze their emotional content through lyrics.

## Installation

### Prerequisites

- Python 3.8 or higher
- PySpark (for data processing)
- Genius API access token ([Get one here](https://genius.com/api-clients))

### Setup

1. Clone the repository:
```bash
git clone https://github.com/lingtouyangLeo/moodify.git
cd moodify
```

2. Install required packages:
```bash
pip install pandas transformers torch lyricsgenius pyspark tqdm
```

3. Configure Genius API:
   - Replace the `client_access_token` in `notebook/lyrics_scraper.py` with your own Genius API token

## Code Execution Instructions

The project pipeline consists of four main stages. Follow these steps in order:

### Stage 1: Extract Top 1000 Songs

**File**: `notebook/getTopKHitSongs.ipynb`

**Purpose**: Extract the most popular tracks from the Spotify Million Playlist Dataset.

**Steps**:
1. Download the Spotify Million Playlist Dataset from [AICrowd](https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge)
2. Unzip the dataset files
3. Open `getTopKHitSongs.ipynb` in Jupyter Notebook or VS Code
4. Run all cells sequentially
5. The script will:
   - Initialize a PySpark session
   - Load all JSON playlist files
   - Explode playlists and tracks into individual rows
   - Count track occurrences across all playlists
   - Export the top 1000 tracks to `data/top1000HitSongs.json`

**Output**: `data/top1000HitSongs.json` (newline-delimited JSON file)

### Stage 2: Scrape Lyrics

**File**: `notebook/lyrics_scraper.py`

**Purpose**: Fetch lyrics for all top 1000 songs using the Genius API.

**Steps**:
1. Ensure you have configured your Genius API token in the script
2. Run the script:
```bash
python notebook/lyrics_scraper.py
```
3. The script features:
   - **Checkpoint system**: Saves progress every 100 songs
   - **Resume capability**: Automatically resumes from where it left off
   - **Rate limiting**: 3-6 second delay between requests
   - **Error handling**: Records songs that fail to fetch

**Output**: `data/tracks_with_lyrics.csv`

**Notes**: 
- The script may take several hours depending on API rate limits
- You can safely stop and restart the script; it will resume from the last checkpoint
- Set `MAX_SONGS` in the script to limit processing for testing purposes

### Stage 3: Clean Lyrics

**File**: `notebook/lyrics_clean.py`

**Purpose**: Preprocess and normalize lyrics text for NLP analysis.

**Steps**:
1. Run the cleaning script:
```bash
python notebook/lyrics_clean.py
```
2. The script performs:
   - Removal of non-lyric content (credits, metadata, section headers)
   - Elimination of stage directions like `[Chorus]`, `[Verse 1]`
   - Filtering of parenthetical comments (keeping emotional shouts)
   - Text normalization (quotation marks, whitespace, casing)
   - Optional lowercasing for consistency

**Output**: `data/tracks_with_lyrics_cleaned.csv`

### Stage 4: Emotion Classification

**File**: `notebook/NLP_Mood.ipynb`

**Purpose**: Classify songs by emotional content and generate mood-based playlists.

**Steps**:
1. Install transformers and PyTorch:
```bash
pip install transformers torch
```
2. Open `NLP_Mood.ipynb` in Jupyter Notebook or VS Code
3. Run all cells sequentially
4. The notebook will:
   - Load cleaned lyrics data
   - Initialize Facebook's BART-large-MNLI zero-shot classifier
   - Classify each song across five emotions: happy, sad, angry, relaxed, energetic
   - Generate emotion scores and predict dominant emotion
   - Create a sample mood-based playlist (10-20 songs)

**Output**: `tracks_with_emotions.csv` (contains emotion scores for all tracks)

**Notes**:
- First run will download the BART-large-MNLI model (~1.6GB)
- Processing 1000 songs takes approximately 30-60 minutes depending on hardware
- GPU acceleration is recommended but not required

## High-Level Code Logic

### 1. Data Extraction (`getTopKHitSongs.ipynb`)

```
Input: Spotify Million Playlist Dataset (JSON files)
│
├─ Initialize PySpark Session
├─ Load multi-line JSON files
├─ Explode playlists array → one row per playlist
├─ Explode tracks array → one row per track
├─ Extract (track_name, artist_name) pairs
├─ Group by track and count occurrences
├─ Sort by play_count descending
└─ Export top 1000 tracks to JSON
│
Output: top1000HitSongs.json
```

**Key Logic**: Uses distributed processing with PySpark to efficiently handle large-scale playlist data. Groups tracks by exact name and artist matches, then ranks by frequency across all playlists.

### 2. Lyrics Scraping (`lyrics_scraper.py`)

```
Input: top1000HitSongs.json
│
├─ Initialize Genius API client
├─ Load existing CSV (if resuming)
├─ Build processed songs set (success + failures)
│
For each song:
│  ├─ Check if already processed → skip
│  ├─ Query Genius API with (track_name, artist_name)
│  ├─ Extract lyrics or record error
│  ├─ Append to results list
│  ├─ Update processed sets
│  ├─ Save checkpoint every 100 songs
│  └─ Sleep 3-6 seconds (rate limiting)
│
└─ Save final CSV with all results
│
Output: tracks_with_lyrics.csv
```

**Key Logic**: Implements robust error handling and checkpointing to handle long-running API operations. Tracks both successful fetches and failures to avoid redundant requests across multiple runs.

### 3. Lyrics Cleaning (`lyrics_clean.py`)

```
Input: tracks_with_lyrics.csv
│
For each song's lyrics:
│  ├─ Split into lines
│  │
│  For each line:
│  │  ├─ Remove non-lyric keywords (credits, metadata)
│  │  ├─ Remove section headers [Chorus], [Verse 1]
│  │  ├─ Filter stage comments (Bridge), (Background Vocals)
│  │  ├─ Keep emotional shouts (yeah), (oh no)
│  │  └─ Normalize whitespace and punctuation
│  │
│  ├─ Merge broken punctuation lines
│  ├─ Normalize quotation marks
│  ├─ Convert to lowercase (optional)
│  └─ Return cleaned text
│
└─ Save cleaned lyrics to new column
│
Output: tracks_with_lyrics_cleaned.csv
```

**Key Logic**: Applies rule-based text processing to remove non-semantic content while preserving emotional expressions. Uses keyword matching and regex patterns to distinguish between structural annotations and meaningful lyrical content.

### 4. Emotion Classification (`NLP_Mood.ipynb`)

```
Input: tracks_with_lyrics_cleaned.csv
│
├─ Load cleaned lyrics
├─ Filter valid lyrics (length > 20 chars)
├─ Initialize zero-shot classifier (BART-large-MNLI)
│
Define emotion labels: [happy, sad, angry, relaxed, energetic]
│
For each song:
│  ├─ Truncate lyrics to 1000 chars
│  ├─ Run zero-shot classification
│  │   └─ Model assigns probability to each emotion label
│  ├─ Extract scores for all emotions
│  ├─ Determine dominant emotion (highest score)
│  └─ Store results
│
├─ Create emotion score columns (score_happy, score_sad, etc.)
├─ Save annotated dataset
│
Playlist Generation:
│  ├─ Sample k songs (10-20) randomly
│  ├─ Calculate mean emotion scores
│  ├─ Identify dominant mood
│  └─ Return mood-based playlist
│
Output: tracks_with_emotions.csv + playlist samples
```

**Key Logic**: Leverages transformer-based zero-shot classification to map lyrics to emotional categories without requiring labeled training data. The model computes semantic similarity between lyrics and emotion label descriptions, producing a probability distribution across all emotions. Playlist generation aggregates individual track emotions by averaging scores, enabling mood-consistent recommendations.

### Architecture Flow

```
[Spotify MPD] 
    ↓ PySpark aggregation
[Top 1000 Songs]
    ↓ Genius API
[Raw Lyrics]
    ↓ Text preprocessing
[Clean Lyrics]
    ↓ BART Zero-Shot Classification
[Emotion Scores]
    ↓ Aggregation & sampling
[Mood-Based Playlists]
```

## Project Structure

```
moodify/
├── app.py                             # Flask web application entry point
├── requirements.txt                   # Python package dependencies
├── .env                               # Environment variables (API keys, config)
├── data/
│   ├── top1000HitSongs.json           # Top 1000 tracks from Spotify MPD
│   ├── tracks_with_lyrics.csv         # Tracks with raw lyrics
│   ├── tracks_with_lyrics_cleaned.csv # Tracks with cleaned lyrics
│   └── tracks_with_emotionLabels.csv  # Tracks with emotion classification
├── moodify/                           # Core package modules
│   ├── __init__.py                    # Package initialization
│   ├── lyrics.py                      # Lyrics fetching and processing
│   ├── mood.py                        # Emotion classification logic
│   ├── pipeline.py                    # Data processing pipeline
│   ├── playlist.py                    # Playlist generation
│   ├── spotify.py                     # Spotify API integration
│   └── storage.py                     # Data storage and retrieval
├── notebook/                          # Jupyter notebooks for analysis
│   ├── getTopKHitSongs.ipynb          # Stage 1: Extract top tracks
│   ├── lyrics_scraper.py              # Stage 2: Fetch lyrics from Genius
│   ├── lyrics_clean.py                # Stage 3: Clean lyrics text
│   └── NLP_Mood.ipynb                 # Stage 4: Emotion classification
├── LICENSE                            # MIT License
├── README.md                          # Main project documentation
└── README_for_flaskapp.md             # Flask web application guide
```

## Requirements

- **Python**: 3.12+
- **Core Libraries**:
  - Flask (web framework)
  - pandas (data manipulation)
  - transformers (NLP models)
  - torch (deep learning)
  - lyricsgenius (lyrics API)
  - langdetect (language detection)
  - python-dotenv (environment variables)
  - requests (HTTP client)
  - tqdm (progress bars)

- **Optional for Data Processing**:
  - pyspark (large-scale data processing)

- **APIs**:
  - Genius API access token (for lyrics scraping - [Get one here](https://genius.com/api-clients))
  - Spotify API credentials (optional - for playlist integration)

- **Hardware**:
  - Minimum: 8GB RAM, CPU
  - Recommended: 16GB RAM, NVIDIA GPU for faster emotion classification

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Project Repository**: https://github.com/lingtouyangLeo/moodify

**README URL**: https://github.com/lingtouyangLeo/moodify#code-execution-instructions
