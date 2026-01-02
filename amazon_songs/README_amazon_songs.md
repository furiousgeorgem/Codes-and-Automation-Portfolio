# Amazon Music Search Automation

Automates Amazon Digital Music searches from a CSV file by opening browser tabs for each track. Eliminates repetitive manual searching during music procurement workflows.

## What It Does

- Reads track data from CSV file
- Auto-detects column names (supports variations like "track"/"song", "artist"/"artists")
- Opens Amazon Digital Music search tabs in your browser
- Rate limits to prevent overwhelming the browser
- Handles URL encoding for special characters

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

Create a `requirements.txt` file:

```
pandas>=2.0.0
```

**Python version:** 3.8+

## Usage

### Basic Usage

```bash
python amazon_songs2.py input.csv
```

### With Custom Limit

```bash
python amazon_songs2.py tracks.csv --limit 25
```

Opens the first 25 tracks only (default is all tracks).

## Input Format

CSV file with columns for track and artist information. The script automatically detects these column names:

**Supported column names:**
- Track: `track`, `song`, `title`, `name`
- Artist: `artist`, `artists`, `performer`

**Example CSV:**

```csv
track,artist
Hotel California,Eagles
Bohemian Rhapsody,Queen
Stairway to Heaven,Led Zeppelin
```

## How It Works

1. Loads CSV using pandas
2. Auto-detects track and artist columns
3. Constructs Amazon Digital Music search URL for each track
4. Opens browser tabs with 0.5 second delay between each

**Amazon search URL format:**
```
https://music.amazon.com/search/[track name] [artist name]
```

## Example

```bash
$ python amazon_songs2.py not_found_tracks.csv --limit 10

Processing 10 tracks...
Opening: Hotel California - Eagles
Opening: Bohemian Rhapsody - Queen
...
Done! Opened 10 search tabs.
```

## Use Case

Built for music procurement teams who need to quickly search Amazon's catalog for multiple tracks. Converts a list of tracks into instant browser searches, saving hours of manual copy-paste work.

## Notes

- Requires browser to allow multiple tabs (disable popup blockers if needed)
- Uses default system browser
- Rate limited to prevent browser overload
- Works on macOS, Windows, and Linux

## Technical Details

**Key features:**
- Pandas for CSV handling
- Flexible column detection with fallback logic
- URL encoding for special characters
- Command-line interface with argparse
- Error handling for missing columns

**Dependencies:**
- `pandas` - CSV file processing
- `webbrowser` - Opens browser tabs (Python standard library)
- `urllib.parse` - URL encoding (Python standard library)
