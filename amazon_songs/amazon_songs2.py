#!/usr/bin/env python3
"""
Amazon Music Search Automation

Opens Amazon search tabs for songs listed in a CSV file. Useful for bulk music procurement.

Usage:
    python amazon_songs.py <csv_file> [options]

Example:
    python amazon_songs.py not_found_tracks.csv --limit 25 --song-col "track" --artist-col "artist_name"

CSV Requirements:
    Must contain columns for song title and artist name (column names configurable via CLI)
"""

import argparse
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install it with: pip install pandas")
    sys.exit(1)


# Column name variations to search for
TRACK_COLNAMES = ['track', 'tracks', 'song', 'song_name', 'song title', 'song_title', 'title']
ARTIST_COLNAMES = ['artist', 'artists', 'artist_name', 'artist name']
ALBUM_COLNAMES = ['album', 'albums', 'album_name', 'album name', 'album_title', 'album title']


def find_column(possible_names, columns):
    """
    Find a column that matches one of the possible names (case-insensitive).
    Returns the original column name from the dataframe.
    """
    # Create lowercase mapping
    lower_to_original = {col.strip().lower(): col for col in columns}
    
    # Try exact match first
    for name in possible_names:
        if name.lower() in lower_to_original:
            return lower_to_original[name.lower()]
    
    # Try partial match (e.g., 'track' in 'track_name')
    for col in columns:
        col_lower = col.strip().lower()
        for name in possible_names:
            if name.lower() in col_lower:
                return col
    
    return None


def open_amazon_searches(csv_path, limit=None, delay=0.5):
    """
    Open Amazon Digital Music search tabs for each song in the CSV.
    
    Args:
        csv_path: Path to CSV file
        limit: Maximum number of tabs to open (None for all)
        delay: Seconds to wait between opening tabs (prevents browser overload)
    """
    # Validate file exists
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Load CSV
    print(f"📂 Loading CSV: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV: {e}")
    
    # Auto-detect columns
    print("🔎 Detecting columns...")
    track_col = find_column(TRACK_COLNAMES, df.columns)
    artist_col = find_column(ARTIST_COLNAMES, df.columns)
    album_col = find_column(ALBUM_COLNAMES, df.columns)
    
    # Validate required columns exist
    if not track_col:
        raise ValueError(f"Could not find track/song column. Available columns: {list(df.columns)}")
    if not artist_col:
        raise ValueError(f"Could not find artist column. Available columns: {list(df.columns)}")
    
    print(f"✅ Found columns - Track: '{track_col}', Artist: '{artist_col}'{f', Album: {album_col}' if album_col else ''}")
    
    # Apply limit if specified
    if limit:
        df = df.head(limit)
        print(f"⚠️  Limiting to first {limit} rows")
    
    print(f"🎵 Opening {len(df)} Amazon Digital Music search tabs...\n")
    
    # Open tabs
    opened = 0
    for idx, row in df.iterrows():
        track = str(row[track_col]).strip()
        artist = str(row[artist_col]).strip()
        
        # Skip empty rows
        if not track or track == 'nan' or not artist or artist == 'nan':
            print(f"⚠️  Skipping row {idx + 1}: missing song or artist")
            continue
        
        # Build search query (include album if available)
        if album_col and pd.notna(row[album_col]):
            album = str(row[album_col]).strip()
            search_query = quote_plus(f"{track} {artist} {album}")
        else:
            search_query = quote_plus(f"{track} {artist}")
        
        # Amazon Digital Music category URL
        url = f"https://www.amazon.com/s?k={search_query}&i=digital-music"
        
        print(f"[{opened + 1}/{len(df)}] Opening: {track} - {artist}")
        webbrowser.open(url)
        opened += 1
        
        # Small delay to prevent overwhelming the browser
        if delay > 0 and opened < len(df):
            time.sleep(delay)
    
    print(f"\n✅ Done! Opened {opened} tabs")


def main():
    parser = argparse.ArgumentParser(
        description='Open Amazon Digital Music search tabs for songs in a CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python amazon_songs2.py tracks.csv

  # Limit to first 10 songs
  python amazon_songs2.py tracks.csv --limit 10

  # No delay between tabs
  python amazon_songs2.py tracks.csv --delay 0

Column Detection:
  The script automatically detects columns with names like:
  - Track/Song: 'track', 'tracks', 'song', 'song_name', 'title', etc.
  - Artist: 'artist', 'artists', 'artist_name', etc.
  - Album: 'album', 'albums', 'album_name', etc. (optional)
        """
    )
    
    parser.add_argument('csv_file', help='Path to CSV file with song/artist data')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of tabs to open (default: no limit)')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Seconds to wait between opening tabs (default: 0.5)')
    
    args = parser.parse_args()
    
    try:
        open_amazon_searches(
            csv_path=args.csv_file,
            limit=args.limit,
            delay=args.delay
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)


if __name__ == '__main__':
    main()
