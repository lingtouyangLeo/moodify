# Moodify

An emotion-aware music recommendation system that analyzes song lyrics to classify tracks by emotional content and generate mood-based playlists.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Dataset](#dataset)
- [Installation](#installation)
- [Code Execution Instructions](#code-execution-instructions)
- [High-Level Code Logic](#high-level-code-logic)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [License](#license)

## Project Overview

Moodify is a music recommendation system that leverages Natural Language Processing (NLP) to analyze song lyrics and classify tracks based on emotional content. The system processes data from the Spotify Million Playlist Dataset, extracts lyrics, and uses a fine-tuned DistilRoBERTa emotion classification model to assign emotional scores to each song. This enables mood-based playlist generation and emotion-aware music recommendations with evaluation metrics.

## Features

- **Data Processing**: Extract top 1000 hit songs from Spotify Million Playlist Dataset using PySpark
- **Lyrics Extraction**: Automated lyrics scraping from Genius API
- **Language Filtering**: Filter non-English songs using language detection
- **Text Cleaning**: Comprehensive lyrics preprocessing and normalization
- **Emotion Analysis**: Multi-label emotion classification using fine-tuned DistilRoBERTa model
- **Model Evaluation**: Confusion matrix and accuracy metrics for model performance
- **Mood-Based Playlists**: Generate playlists based on five emotion categories: happy, sad, angry, relaxed, and energetic
- **Smart Recommendations**: Recommend similar songs based on detected mood with duplication avoidance

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
pip install pandas transformers torch lyricsgenius pyspark tqdm langdetect
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

**Purpose**: Preprocess and normalize lyrics text for NLP analysis, filtering out non-English songs.

**Steps**:
1. Ensure langdetect is installed:
```bash
pip install langdetect
```
2. Run the cleaning script:
```bash
python notebook/lyrics_clean.py
```
3. The script performs:
   - **Language Detection**: Filters out non-English songs using `langdetect` library (90% confidence threshold)
   - Removal of non-lyric content (URLs, credits, metadata)
   - Elimination of structural markers like `[Chorus]`, `[Verse 1]`
   - Filtering of stage directions `(Verse)`, `(Chorus)`, `(Bridge)` while keeping emotional expressions `(yeah)`, `(oh no)`
   - Text normalization (lowercase, whitespace, special characters)
   - Removal of songs with cleaned lyrics shorter than 20 characters

**Output**: `data/tracks_with_lyrics_cleaned.csv` (English songs only)

**Configuration**:
- `LANGDETECT_EN_PROB_THRESHOLD = 0.90`: Minimum probability to classify as English
- `MIN_CLEAN_LENGTH = 20`: Minimum character count for cleaned lyrics

### Stage 4: Emotion Classification and Evaluation

**File**: `notebook/NLP_Mood.ipynb`

**Purpose**: Classify songs by emotional content, evaluate model performance, and generate mood-based recommendations.

**Steps**:
1. Install required packages:
```bash
pip install transformers torch scikit-learn seaborn matplotlib
```
2. Open `NLP_Mood.ipynb` in Jupyter Notebook or VS Code
3. Run all cells sequentially
4. The notebook performs:
   - **Cell 1**: Install dependencies
   - **Cell 2**: Emotion classification
     - Load cleaned lyrics data from `tracks_with_emotionLabels.csv`
     - Initialize DistilRoBERTa emotion model (`j-hartmann/emotion-english-distilroberta-base`)
     - Classify lyrics into 7 base emotions (anger, disgust, fear, joy, neutral, sadness, surprise)
     - Map to 5 target emotions:
       - `happy` ← joy
       - `sad` ← sadness
       - `angry` ← anger
       - `relaxed` ← neutral
       - `energetic` ← 0.6 × surprise + 0.4 × joy
     - Process in batches (batch_size=16) with GPU acceleration if available
   - **Cell 3**: Model evaluation
     - Calculate classification accuracy
     - Generate confusion matrix visualization
   - **Cell 4**: Playlist generation
     - Sample 10-20 songs randomly
     - Calculate dominant mood by averaging emotion scores
   - **Cell 5**: Smart recommendation
     - Recommend 5-10 songs matching the playlist mood
     - Avoid duplicate recommendations

**Output**: 
- `track_with_pred.csv` (contains 5 emotion scores + predicted emotion for all tracks)
- Confusion matrix visualization
- Sample playlist with mood analysis
- Mood-based recommendations

**Notes**:
- First run will download the DistilRoBERTa model (~290MB, much smaller than BART)
- Processing 1000 songs takes approximately 10-20 minutes with CPU, 2-5 minutes with GPU
- GPU acceleration is recommended for faster processing
- Model requires labeled data in `tracks_with_emotionLabels.csv` for evaluation (Cell 3)

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
├─ Filter Non-English Songs:
│  └─ Use langdetect library to detect language
│     └─ Keep only songs with ≥90% English probability
│
For each song's lyrics:
│  ├─ Split into lines
│  │
│  For each line:
│  │  ├─ Remove URLs (http://, www.)
│  │  ├─ Remove section headers [Chorus], [Verse 1]
│  │  ├─ Filter stage comments (Bridge), (Background Vocals)
│  │  ├─ Keep emotional shouts (yeah), (oh no)
│  │  └─ Normalize whitespace and punctuation
│  │
│  ├─ Convert to lowercase
│  ├─ Remove special characters (keep a-z, 0-9, basic punctuation)
│  ├─ Collapse multiple spaces and blank lines
│  └─ Return cleaned text
│
├─ Filter songs with cleaned lyrics < 20 characters
└─ Save cleaned English lyrics
│
Output: tracks_with_lyrics_cleaned.csv (English only)
```

**Key Logic**: Implements language detection using `langdetect` to filter out non-English songs before text processing. The library analyzes character n-gram patterns to estimate language probability with deterministic results (seed-fixed). Then applies rule-based text processing to remove non-semantic content while preserving emotional expressions. Uses keyword matching and regex patterns to distinguish between structural annotations and meaningful lyrical content.

### 4. Emotion Classification (`NLP_Mood.ipynb`)

```
Input: tracks_with_emotionLabels.csv (cleaned lyrics)
│
├─ Load cleaned lyrics
├─ Filter valid lyrics (length > 20 chars)
├─ Initialize DistilRoBERTa emotion classifier
│   └─ Model: j-hartmann/emotion-english-distilroberta-base
│   └─ Fine-tuned on 6 emotion datasets
│
Base emotions (7): [anger, disgust, fear, joy, neutral, sadness, surprise]
│
Batch Processing (batch_size=16):
│  For each batch:
│  │  ├─ Truncate lyrics to 512 tokens
│  │  ├─ Run emotion classification
│  │  │   └─ Model outputs scores for all 7 base emotions
│  │  ├─ Map 7 base emotions → 5 target emotions:
│  │  │   ├─ happy = joy
│  │  │   ├─ sad = sadness
│  │  │   ├─ angry = anger
│  │  │   ├─ relaxed = neutral
│  │  │   └─ energetic = 0.6×surprise + 0.4×joy
│  │  ├─ Determine dominant emotion (max score)
│  │  └─ Store: 5 scores + pred_emotion + base_emotion_raw
│
├─ Save results to track_with_pred.csv
│
Model Evaluation (if labeled data available):
│  ├─ Compare predictions vs ground truth
│  ├─ Calculate accuracy
│  └─ Generate confusion matrix visualization
│
Playlist Generation:
│  ├─ Sample k songs (10-20) randomly
│  ├─ Calculate mean emotion scores across playlist
│  ├─ Identify dominant mood (highest average score)
│  └─ Display playlist with individual emotions
│
Smart Recommendation:
│  ├─ Input: detected mood from playlist
│  ├─ Filter candidates: same pred_emotion OR high score
│  ├─ Exclude songs already in playlist
│  ├─ Sort by mood-specific score (descending)
│  └─ Return top 5-10 recommendations
│
Output: track_with_pred.csv + visualizations + recommendations
```

**Key Logic**: Uses a specialized DistilRoBERTa model fine-tuned on emotion classification tasks, providing more accurate emotion detection than zero-shot approaches. The model outputs probabilities for 7 base emotions, which are then mapped to 5 musically-relevant categories. The `energetic` emotion is computed as a weighted combination of `surprise` and `joy` to capture high-energy tracks. Batch processing with GPU acceleration enables efficient classification of large datasets. The recommendation system filters songs by predicted emotion and ranks them by emotion-specific confidence scores, avoiding duplicates from the original playlist.

### Architecture Flow

```
[Spotify MPD] 
    ↓ PySpark aggregation
[Top 1000 Songs]
    ↓ Genius API
[Raw Lyrics]
    ↓ Language detection (langdetect)
[English Lyrics Only]
    ↓ Text preprocessing & cleaning
[Clean Lyrics]
    ↓ DistilRoBERTa Emotion Classification
[7 Base Emotions] → [5 Target Emotions]
    ↓ Model evaluation (if labels available)
[Emotion Scores + Performance Metrics]
    ↓ Aggregation & sampling
[Mood-Based Playlists]
    ↓ Mood-aware filtering
[Smart Recommendations]
```

## Project Structure

```
moodify/
├── data/
│   ├── top1000HitSongs.json           # Top 1000 tracks from Spotify MPD
│   ├── tracks_with_lyrics.csv         # Tracks with raw lyrics
│   └── tracks_with_lyrics_cleaned.csv # Tracks with cleaned lyrics
├── notebook/
│   ├── getTopKHitSongs.ipynb          # Stage 1: Extract top tracks
│   ├── lyrics_scraper.py              # Stage 2: Fetch lyrics from Genius
│   ├── lyrics_clean.py                # Stage 3: Clean lyrics text
│   └── NLP_Mood.ipynb                 # Stage 4: Emotion classification
├── LICENSE
└── README.md                          # This file
```

## Requirements

- **Python**: 3.12+
- **Core Libraries**:
  - pandas
  - transformers
  - torch
  - lyricsgenius
  - pyspark
  - tqdm
  - langdetect
  - scikit-learn (for evaluation)
  - seaborn (for visualization)
  - matplotlib (for plotting)

- **APIs**:
  - Genius API access token (free registration)

- **Hardware**:
  - Minimum: 8GB RAM, CPU
  - Recommended: 16GB RAM, NVIDIA GPU for faster inference

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Project Repository**: https://github.com/lingtouyangLeo/moodify

**README URL**: https://github.com/lingtouyangLeo/moodify#code-execution-instructions
