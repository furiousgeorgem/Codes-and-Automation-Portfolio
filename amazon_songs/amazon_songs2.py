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


def open_amazon_searches(csv_path, song_col='song_title', artist_col='artist_name', limit=None, delay=0.5):
    """
    Open Amazon search tabs for each song in the CSV.
    
    Args:
        csv_path: Path to CSV file
        song_col: Name of the song title column
        artist_col: Name of the artist column
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
    
    # Validate columns exist
    if song_col not in df.columns:
        raise ValueError(f"Column '{song_col}' not found. Available columns: {list(df.columns)}")
    if artist_col not in df.columns:
        raise ValueError(f"Column '{artist_col}' not found. Available columns: {list(df.columns)}")
    
    # Apply limit if specified
    if limit:
        df = df.head(limit)
        print(f"⚠️  Limiting to first {limit} rows")
    
    print(f"🎵 Opening {len(df)} Amazon search tabs...\n")
    
    # Open tabs
    opened = 0
    for idx, row in df.iterrows():
        song = str(row[song_col]).strip()
        artist = str(row[artist_col]).strip()
        
        # Skip empty rows
        if not song or song == 'nan' or not artist or artist == 'nan':
            print(f"⚠️  Skipping row {idx + 1}: missing song or artist")
            continue
        
        # URL encode and create search URL
        search_query = quote_plus(f"{song} {artist}")
        url = f"https://www.amazon.com/s?k={search_query}"
        
        print(f"[{opened + 1}/{len(df)}] Opening: {song} - {artist}")
        webbrowser.open(url)
        opened += 1
        
        # Small delay to prevent overwhelming the browser
        if delay > 0 and opened < len(df):
            time.sleep(delay)
    
    print(f"\n✅ Done! Opened {opened} tabs")


def main():
    parser = argparse.ArgumentParser(
        description='Open Amazon search tabs for songs in a CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python amazon_songs.py tracks.csv

  # Limit to first 10 songs
  python amazon_songs.py tracks.csv --limit 10

  # Custom column names
  python amazon_songs.py data.csv --song-col "Title" --artist-col "Artist Name"

  # No delay between tabs
  python amazon_songs.py tracks.csv --delay 0
        """
    )
    
    parser.add_argument('csv_file', help='Path to CSV file with song/artist data')
    parser.add_argument('--song-col', default='song_title', 
                       help='Name of song title column (default: song_title)')
    parser.add_argument('--artist-col', default='artist_name',
                       help='Name of artist column (default: artist_name)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of tabs to open (default: no limit)')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Seconds to wait between opening tabs (default: 0.5)')
    
    args = parser.parse_args()
    
    try:
        open_amazon_searches(
            csv_path=args.csv_file,
            song_col=args.song_col,
            artist_col=args.artist_col,
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