#!/usr/bin/env python3
"""
Compare two station snapshot CSVs and print/post changes.

Usage:
  python3 furious_reporter2.py <yesterday.csv> <today.csv> [--slack]

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
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from typing import Dict, Tuple, Optional, List

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

# Optional Slack deps
try:
    import requests  # pip install requests
except Exception:
    requests = None

# ----------------- Helpers -----------------

def _norm(s: str) -> str:
    # Normalize headers & candidates the same way: lowercase and drop non-alnum/space
    return "".join(ch.lower() for ch in s if ch.isalnum() or ch.isspace()).strip()

def find_column(header: List[str], candidates: List[str]) -> Optional[str]:
    norm_map = {_norm(h): h for h in header}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    return None

def parse_int(x) -> int:
    if x is None:
        return 0
    if isinstance(x, (int, float)):
        return int(x)
    s = str(x).replace(",", "").strip()
    if s == "":
        return 0
    try:
        return int(float(s))
    except ValueError:
        return 0

def parse_float(x) -> float:
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).replace(",", "").strip()
    if s == "":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

def to_hours2_from_row(row: dict, hours_col: Optional[str], seconds_col: Optional[str]) -> float:
    if hours_col and row.get(hours_col) not in (None, ""):
        return round(parse_float(row[hours_col]), 2)
    if seconds_col and row.get(seconds_col) not in (None, ""):
        return round(parse_int(row[seconds_col]) / 3600.0, 2)
    return 0.0

def format_update_line(name: str, b_songs: int, b_hours: float, a_songs: int, a_hours: float) -> str:
    d_hours = round(a_hours - b_hours, 2)
    return f"[UPDATE] {name}: {b_songs} songs, {b_hours:.2f} hrs → {a_songs} songs, {a_hours:.2f} hrs (+{d_hours:.2f} hrs)"

# ------------- Core CSV logic -------------

def load_snapshot_csv(path: str) -> Dict[str, Tuple[int, float]]:
    """
    Returns: { station_name: (songs, hours) }
    If multiple rows per station, aggregates by summing (defensive).
    """
    out_songs: Dict[str, int] = defaultdict(int)
    out_hours: Dict[str, float] = defaultdict(float)

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError(f"{path}: missing header row")

        cols = reader.fieldnames

        station_col = find_column(cols, [
            "station", "name", "station_name", "stationname"
        ])
        songs_col = find_column(cols, [
            "song_count", "songs", "songcount", "song count", "song_count_total"
        ])
        hours_col = find_column(cols, [
            "total_hours", "hours", "station duration (in hours)", "stationdurationinhours"
        ])
        seconds_col = find_column(cols, [
            "total_seconds", "seconds", "duration_seconds", "totalseconds"
        ])

        if not station_col:
            raise RuntimeError(f"{path}: could not find station/name column. Found headers: {reader.fieldnames}")
        if not songs_col:
            raise RuntimeError(f"{path}: could not find song count column. Found headers: {reader.fieldnames}")
        if not hours_col and not seconds_col:
            raise RuntimeError(f"{path}: need either total_hours or total_seconds column. Found headers: {reader.fieldnames}")

        for row in reader:
            name = str(row.get(station_col, "")).strip()
            if not name:
                continue
            songs = parse_int(row.get(songs_col))
            hours = to_hours2_from_row(row, hours_col, seconds_col)
            out_songs[name] += songs
            out_hours[name] += hours

    return {name: (out_songs[name], round(out_hours[name], 2)) for name in out_songs.keys() | out_hours.keys()}

def diff_snapshots(prev: Dict[str, Tuple[int, float]], curr: Dict[str, Tuple[int, float]]) -> List[str]:
    lines = []
    all_names = set(prev.keys()) | set(curr.keys())
    for name in sorted(all_names):
        b_songs, b_hours = prev.get(name, (0, 0.0))
        a_songs, a_hours = curr.get(name, (0, 0.0))
        if b_songs != a_songs or round(b_hours, 2) != round(a_hours, 2):
            lines.append(format_update_line(name, b_songs, round(b_hours, 2), a_songs, round(a_hours, 2)))
    return lines

# --------------- Slack posting ------------

WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "").strip()
BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "").strip()
CHANNEL = os.getenv("SLACK_CHANNEL", "").strip()

def post_to_slack(lines: List[str], title: str):
    text = f"{title}\n" + ("\n".join(lines) if lines else "[info] no changes.")

    # Prefer webhook
    if WEBHOOK:
        if not requests:
            print("[warn] requests not installed; cannot post via webhook.", file=sys.stderr)
            return
        r = requests.post(WEBHOOK, json={"text": text}, timeout=15)
        r.raise_for_status()
        return

    # Fallback to bot token
    if BOT_TOKEN and CHANNEL:
        if not requests:
            print("[warn] requests not installed; cannot post via bot token.", file=sys.stderr)
            return
        # Chunk to avoid Slack length limits
        chunks = []
        current = ""
        for line in text.splitlines():
            if len(current) + len(line) + 1 > 3500:
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

# ------------------- CLI ------------------

def main():
    ap = argparse.ArgumentParser(description="Compare two station CSV snapshots and print/post changes")
    ap.add_argument("yesterday_csv", help="Path to yesterday's CSV (older)")
    ap.add_argument("today_csv", help="Path to today's CSV (newer)")
    ap.add_argument("--slack", action="store_true", help="Also post the result to Slack (Webhook or Bot)")
    args = ap.parse_args()

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
        try:
            post_to_slack(changes, title)
        except Exception as e:
            print(f"[warn] Slack post failed: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()