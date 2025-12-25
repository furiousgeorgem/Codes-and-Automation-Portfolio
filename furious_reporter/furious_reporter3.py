#!/usr/bin/env python3
"""
Compare two station snapshot CSVs and print/post changes.

Usage:
  python3 furious_reporter3.py <yesterday.csv> <today.csv> [--slack]

CSV columns (case-insensitive; underscores/spaces ignored):
- Station name: one of ["station","name","station_name","stationname"]
- Song count:   one of ["song_count","songs","songcount","song count","song_count_total"]
- Hours:        one of ["total_hours","hours","station duration (in hours)","stationdurationinhours"]
  OR Seconds:   one of ["total_seconds","seconds","duration_seconds","totalseconds"]

Env (.env or environment):
  SLACK_WEBHOOK_URL=...               # Incoming Webhook (simplest)
  # or:
  SLACK_BOT_TOKEN=xoxb-...            # Bot token fallback
  SLACK_CHANNEL=#channel-or-C123...   # Required if using bot token

Requirements:
  pip install -r requirements.txt
"""

import argparse
import os
import sys
from typing import Dict, Tuple, List

import pandas as pd
import requests
from dotenv import load_dotenv

# Load .env if present
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------
# Constants
# ---------------------------

SLACK_MESSAGE_CHAR_LIMIT = 3500  # Slack's character limit per message

STATION_COLNAMES = ["station", "name", "station_name", "stationname"]
SONG_COUNT_COLNAMES = ["song_count", "songs", "songcount", "song count", "song_count_total"]
HOURS_COLNAMES = ["total_hours", "hours", "station duration (in hours)", "stationdurationinhours"]
SECONDS_COLNAMES = ["total_seconds", "seconds", "duration_seconds", "totalseconds"]


# ---------------------------
# Helpers
# ---------------------------

def _norm(s: str) -> str:
    """Normalize column names: lowercase and drop non-alnum/space."""
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch.isspace()).strip()


def find_column(df_columns: List[str], candidates: List[str]) -> str:
    """Find a column that matches one of the candidates (case-insensitive)."""
    norm_map = {_norm(col): col for col in df_columns}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    raise KeyError(f"Column not found. Tried: {candidates}. Available: {list(df_columns)}")


def format_update_line(name: str, b_songs: int, b_hours: float, a_songs: int, a_hours: float) -> str:
    """Format a single station update line."""
    d_hours = round(a_hours - b_hours, 2)
    return f"[UPDATE] {name}: {b_songs} songs, {b_hours:.2f} hrs → {a_songs} songs, {a_hours:.2f} hrs (+{d_hours:.2f} hrs)"


# ---------------------------
# Core CSV logic
# ---------------------------

def load_snapshot_csv(path: str) -> Dict[str, Tuple[int, float]]:
    """
    Load a station snapshot CSV and return: { station_name: (songs, hours) }
    If multiple rows per station, aggregates by summing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    # Load with pandas
    df = pd.read_csv(path, keep_default_na=False)
    
    # Find columns
    station_col = find_column(df.columns, STATION_COLNAMES)
    songs_col = find_column(df.columns, SONG_COUNT_COLNAMES)
    
    # Try to find hours or seconds column
    hours_col = None
    seconds_col = None
    try:
        hours_col = find_column(df.columns, HOURS_COLNAMES)
    except KeyError:
        pass
    
    try:
        seconds_col = find_column(df.columns, SECONDS_COLNAMES)
    except KeyError:
        pass
    
    if not hours_col and not seconds_col:
        raise RuntimeError(f"{path}: need either total_hours or total_seconds column. Found: {list(df.columns)}")
    
    # Convert seconds to hours if needed
    if hours_col:
        df['hours'] = pd.to_numeric(df[hours_col], errors='coerce').fillna(0)
    else:
        df['hours'] = pd.to_numeric(df[seconds_col], errors='coerce').fillna(0) / 3600.0
    
    # Convert songs to int
    df['songs'] = pd.to_numeric(df[songs_col], errors='coerce').fillna(0).astype(int)
    
    # Group by station and sum (handles duplicates)
    result = df.groupby(station_col).agg({'songs': 'sum', 'hours': 'sum'}).to_dict('index')
    
    # Convert to expected format: {station: (songs, hours)}
    return {station: (data['songs'], round(data['hours'], 2)) for station, data in result.items()}


def diff_snapshots(prev: Dict[str, Tuple[int, float]], curr: Dict[str, Tuple[int, float]]) -> List[str]:
    """Compare two snapshots and return list of change descriptions."""
    lines = []
    all_names = set(prev.keys()) | set(curr.keys())
    
    for name in sorted(all_names):
        b_songs, b_hours = prev.get(name, (0, 0.0))
        a_songs, a_hours = curr.get(name, (0, 0.0))
        
        if b_songs != a_songs or round(b_hours, 2) != round(a_hours, 2):
            lines.append(format_update_line(name, b_songs, round(b_hours, 2), a_songs, round(a_hours, 2)))
    
    return lines


# ---------------------------
# Slack posting
# ---------------------------

WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "").strip()
BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
CHANNEL = os.getenv("SLACK_CHANNEL", "").strip()


def post_to_slack(lines: List[str], title: str):
    """Post changes to Slack via webhook or bot token."""
    text = f"{title}\n" + ("\n".join(lines) if lines else "[info] no changes.")
    
    # Prefer webhook
    if WEBHOOK:
        r = requests.post(WEBHOOK, json={"text": text}, timeout=15)
        r.raise_for_status()
        return
    
    # Fallback to bot token
    if BOT_TOKEN and CHANNEL:
        # Chunk to avoid Slack length limits
        chunks = []
        current = ""
        for line in text.splitlines():
            if len(current) + len(line) + 1 > SLACK_MESSAGE_CHAR_LIMIT:
                chunks.append(current)
                current = ""
            current += (line + "\n")
        if current:
            chunks.append(current)
        
        for chunk in chunks:
            r = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {BOT_TOKEN}"},
                json={"channel": CHANNEL, "text": chunk},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                raise RuntimeError(f"Slack API error: {data}")
        return
    
    print("[info] Slack not configured. Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN + SLACK_CHANNEL in .env")


# ---------------------------
# CLI
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Compare two station CSV snapshots and print/post changes")
    ap.add_argument("yesterday_csv", help="Path to yesterday's CSV (older)")
    ap.add_argument("today_csv", help="Path to today's CSV (newer)")
    ap.add_argument("--slack", action="store_true", help="Also post the result to Slack (Webhook or Bot)")
    args = ap.parse_args()
    
    try:
        prev = load_snapshot_csv(args.yesterday_csv)
        curr = load_snapshot_csv(args.today_csv)
        
        changes = diff_snapshots(prev, curr)
        
        if changes:
            for line in changes:
                print(line)
        else:
            print("[info] no changes.")
        
        if args.slack:
            title = f"*PCC Station Updates:* {os.path.basename(args.yesterday_csv)} → {os.path.basename(args.today_csv)}"
            post_to_slack(changes, title)
            
    except (FileNotFoundError, KeyError, RuntimeError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Slack post failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
