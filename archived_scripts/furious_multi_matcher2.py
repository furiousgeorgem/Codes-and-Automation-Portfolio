#!/usr/bin/env python3
"""
Multi-curation matcher vs. library with:
- Robust column detection and canonical columns (track/artist/album)
- Safer CSV reads (preserve empty strings)
- Candidate blocking (by clean artist + first token) for huge speedups
- Token and n-gram signals + tunable weights/thresholds via CLI
- Optional conservative title tail trimming (instead of trimming after any dash/colon)
- Progress logging and consistent outputs

Usage:
  python3 furious_multi_matcher_v2.py <library.csv> <curation1.csv> [<curation2.csv> ...]

Optional flags:
  --min_score 0.85            Minimum fuzzy score to count as a match
  --artist_weight 0.45        Weight for artist similarity
  --title_weight 0.35         Weight for title similarity
  --ngram_weight 0.20         Combined weight for ngram_title + ngram_artist (split evenly)
  --album_weight 0.20         Additional album contribution (only when album present on both sides)
  --trim_aggressive           Apply conservative tail trimming rules (remaster/live/etc)
  --workers 8                 Thread workers for parallelism

Output per curation:
  <curation_base>_matched_v2.csv
  <curation_base>_not_found_v2.csv
"""

import argparse
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict

import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from rapidfuzz.fuzz import ratio, token_set_ratio

# ---------------------------
# Cleaning helpers
# ---------------------------

def clean_text_base(text: str) -> str:
    """Basic normalization, remove parentheses/brackets, replace & with and, strip punctuation, lower.
    This version does NOT chop at dashes/colons.
    """
    if pd.isna(text):
        return ''
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    # remove anything in (...) or [...] (user's preferred rule)
    text = re.sub(r"\s*[\(\[].*?[\)\]]", '', text)
    # feature tails like 'feat. ...'
    text = re.sub(r"feat\.? .*", '', text, flags=re.I)
    # & -> and
    text = re.sub(r"&", 'and', text)
    # remove non-alnum/space
    text = re.sub(r"[^a-zA-Z0-9 ]", '', text)
    return text.strip().lower()


def clean_text_tail_conservative(text: str) -> str:
    """Optional conservative tail trimming: remove common edition tails after dashes/colons.
    Safer than nuking everything after first dash/colon.
    """
    if pd.isna(text):
        return ''
    s = str(text)
    # Trim common suffixes like ' - remaster', ': live', '- radio edit', etc.
    s = re.sub(r"\s*[-:\u2013\u2014]\s*(single|remaster(ed)?( \d{2,4})?|remix|mix|live|radio edit|explicit|clean|version|deluxe).*$",
               '', s, flags=re.I)
    return s


def clean_text(text: str, trim_aggressive: bool = False) -> str:
    if trim_aggressive:
        text = clean_text_tail_conservative(text)
    return clean_text_base(text)


def ngram_dist(a: str, b: str, trim_aggressive: bool = False) -> float:
    sa = set(clean_text(a, trim_aggressive).split())
    sb = set(clean_text(b, trim_aggressive).split())
    if not sa or not sb:
        return 0.0
    return len(sa.intersection(sb)) / max(len(sa), len(sb))


# ---------------------------
# Column detection
# ---------------------------

TRACK_COLNAMES = ['track', 'tracks', 'song', 'song_name', 'song title', 'song_title']
ARTIST_COLNAMES = ['artist', 'artists', 'artist_name']
ALBUM_COLNAMES = ['album', 'album_name', 'album title', 'album_title']


def find_column(possible_names, columns):
    """Return the ORIGINAL column name from `columns` that matches one of `possible_names`.
    First tries exact lowercased match, then soft contains match (e.g., 'track name').
    Raises KeyError if not found.
    """
    # Map lower->original
    norm = {c.strip().lower(): c for c in columns}
    # exact match first
    for name in possible_names:
        key = name.lower()
        if key in norm:
            return norm[key]
    # soft contains
    for c in columns:
        lc = c.strip().lower()
        if any(name in lc for name in [n.lower() for n in possible_names]):
            return c
    raise KeyError(f"❌ Column not found. Tried: {possible_names}. Available: {list(columns)}")


# ---------------------------
# Matching core
# ---------------------------

def build_match_result(row, lib_row, ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album, match_type):
    return {
        **row,
        'mediaid': lib_row.get('mediaid', ''),
        'matched_track': lib_row.get('track', ''),
        'matched_artist': lib_row.get('artist', ''),
        'matched_album': lib_row.get('album', ''),
        'ratio_title': round(ratio_title, 3),
        'ratio_artist': round(ratio_artist, 3),
        'ratio_album': round(ratio_album, 3),
        'ngram_title': round(ngram_title, 3),
        'ngram_artist': round(ngram_artist, 3),
        'ngram_album': round(ngram_album, 3),
        'match_type': match_type
    }


def compute_scores(row, lib_row, trim_aggressive=False):
    # RapidFuzz ratios
    rt = ratio(row['clean_track'], lib_row['clean_track']) / 100.0
    rt_tok = token_set_ratio(row['clean_track'], lib_row['clean_track']) / 100.0
    ra = ratio(row['clean_artist'], lib_row['clean_artist']) / 100.0
    ra_tok = token_set_ratio(row['clean_artist'], lib_row['clean_artist']) / 100.0
    # average of raw + token_set for robustness
    ratio_title = (rt + rt_tok) * 0.5
    ratio_artist = (ra + ra_tok) * 0.5

    ngram_title = ngram_dist(row['track'], lib_row['track'], trim_aggressive)
    ngram_artist = ngram_dist(row['artist'], lib_row['artist'], trim_aggressive)

    ratio_album = 0.0
    ngram_album = 0.0
    if row.get('clean_album') and lib_row.get('clean_album'):
        rt_al = ratio(row['clean_album'], lib_row['clean_album']) / 100.0
        rt_al_tok = token_set_ratio(row['clean_album'], lib_row['clean_album']) / 100.0
        ratio_album = (rt_al + rt_al_tok) * 0.5
        ngram_album = ngram_dist(row['album'], lib_row['album'], trim_aggressive)

    return ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album


def weighted_score(ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album,
                   title_w, artist_w, ngram_w, album_w):
    # Split ngram weight evenly between title/artist ngrams
    ng_each = (ngram_w / 2.0) if ngram_w > 0 else 0.0
    base = title_w * ratio_title + artist_w * ratio_artist + ng_each * ngram_title + ng_each * ngram_artist
    # Album only contributes if available
    if ratio_album > 0 or ngram_album > 0:
        base += album_w * ((ratio_album + ngram_album) / 2.0)
    return base


def match_row(row, library_keys, library_album_keys, artist_buckets, first_token_buckets,
              album_in_curation, min_score, title_w, artist_w, ngram_w, album_w, trim_aggressive):
    # 1) Exact album key (if curation has album)
    if album_in_curation:
        key_al = f"{row['clean_track']} - {row['clean_artist']} - {row['clean_album']}"
        lib_row = library_album_keys.get(key_al)
        if lib_row is not None:
            ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album = compute_scores(row, lib_row, trim_aggressive)
            return build_match_result(row, lib_row, 1.0, 1.0, 1.0, ngram_title, ngram_artist, ngram_album, 'exact_album')

    # 2) Exact track+artist key
    key = f"{row['clean_track']} - {row['clean_artist']}"
    lib_row = library_keys.get(key)
    if lib_row is not None:
        ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album = compute_scores(row, lib_row, trim_aggressive)
        return build_match_result(row, lib_row, 1.0, 1.0, ratio_album, ngram_title, ngram_artist, ngram_album, 'exact')

    # 3) Candidate pool by artist to avoid full scan
    cands = []
    ca = row['clean_artist']
    cands.extend(artist_buckets.get(ca, []))
    if len(cands) < 10:
        tok = ca.split(' ')[0] if ca else ''
        cands.extend(first_token_buckets.get(tok, []))
    # Dedup while preserving order
    seen = set(); pool = []
    for r in cands:
        rid = int(r.name) if hasattr(r, 'name') else id(r)
        if rid not in seen:
            seen.add(rid); pool.append(r)

    # 4) Fuzzy across candidate pool
    best = None
    best_score = -1.0
    best_parts = None
    for lib_row in pool:
        ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album = compute_scores(row, lib_row, trim_aggressive)
        score = weighted_score(ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album,
                               title_w, artist_w, ngram_w, album_w)
        if score > best_score:
            best_score = score
            best = lib_row
            best_parts = (ratio_title, ratio_artist, ratio_album, ngram_title, ngram_artist, ngram_album)

    if best is not None and best_score >= min_score:
        rt, ra, ral, nt, na, nal = best_parts
        mtype = 'fuzzy_album' if (ral > 0 or nal > 0) and album_in_curation else 'fuzzy'
        return build_match_result(row, best, rt, ra, ral, nt, na, nal, mtype)

    return None


# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description='Match multiple curation CSVs against a library CSV.')
    ap.add_argument('library', help='Path to library CSV')
    ap.add_argument('curations', nargs='+', help='One or more curation CSV paths')
    ap.add_argument('--min_score', type=float, default=0.85, help='Minimum fuzzy score to count as a match (default: 0.85)')
    ap.add_argument('--artist_weight', type=float, default=0.45, help='Weight for artist similarity (default: 0.45)')
    ap.add_argument('--title_weight', type=float, default=0.35, help='Weight for title similarity (default: 0.35)')
    ap.add_argument('--ngram_weight', type=float, default=0.20, help='Combined weight for ngram_title + ngram_artist (default: 0.20)')
    ap.add_argument('--album_weight', type=float, default=0.20, help='Album contribution weight when album present (default: 0.20)')
    ap.add_argument('--trim_aggressive', action='store_true', help='Enable conservative tail trimming (remaster/live/etc)')
    ap.add_argument('--workers', type=int, default=8, help='Thread workers (default: 8)')
    args = ap.parse_args()

    library_path = args.library
    curation_paths = args.curations

    print('📂 Working directory:', os.getcwd())
    print(f'📄 Loading library CSV: {library_path}')
    library = pd.read_csv(library_path, keep_default_na=False)
    print(f'✅ Library loaded: {len(library)} rows')

    # Normalize column name list but keep original names for access
    print('🔎 Detecting track/artist/album columns in library...')
    library_columns = list(library.columns)
    library_track_col = find_column(TRACK_COLNAMES, library_columns)
    library_artist_col = find_column(ARTIST_COLNAMES, library_columns)
    album_in_library = any(col for col in [find for find in [c for c in library_columns if any(a in c.lower() for a in [n.lower() for n in ALBUM_COLNAMES])]])
    library_album_col = None
    try:
        library_album_col = find_column(ALBUM_COLNAMES, library_columns)
        album_in_library = True
    except KeyError:
        album_in_library = False

    print(f"🎵 Track column: {library_track_col} | 👤 Artist column: {library_artist_col} | 💿 Album column: {library_album_col if album_in_library else 'N/A'}")

    # Canonical columns for downstream safety
    library['track'] = library[library_track_col]
    library['artist'] = library[library_artist_col]
    library['album'] = library[library_album_col] if album_in_library else ''

    # Clean and keys for library
    print('🧼 Cleaning track, artist, and album names in library...')
    library['clean_track'] = library['track'].apply(lambda x: clean_text(x, args.trim_aggressive))
    library['clean_artist'] = library['artist'].apply(lambda x: clean_text(x, args.trim_aggressive))
    library['clean_album'] = library['album'].apply(lambda x: clean_text(x, args.trim_aggressive)) if album_in_library else ''

    # Exact-match key dicts (single row per key; last wins). For better duplicate handling you can switch to lists.
    library_keys = {f"{row['clean_track']} - {row['clean_artist']}": row for _, row in library.iterrows()}
    library_album_keys = {f"{row['clean_track']} - {row['clean_artist']} - {row['clean_album']}": row for _, row in library.iterrows()}

    # Candidate buckets for fuzzy matching
    artist_buckets = defaultdict(list)
    for idx, r in library.iterrows():
        artist_buckets[r['clean_artist']].append(r)

    first_token_buckets = defaultdict(list)
    for idx, r in library.iterrows():
        tok = r['clean_artist'].split(' ')[0] if r['clean_artist'] else ''
        first_token_buckets[tok].append(r)

    for curation_path in curation_paths:
        print(f"\n📄 Loading curation CSV: {curation_path}")
        curation = pd.read_csv(curation_path, keep_default_na=False)
        print(f"✅ Curation loaded: {len(curation)} rows")

        # Detect columns
        print('🔎 Detecting track/artist/album columns in curation...')
        cur_cols = list(curation.columns)
        curation_track_col = find_column(TRACK_COLNAMES, cur_cols)
        curation_artist_col = find_column(ARTIST_COLNAMES, cur_cols)
        try:
            curation_album_col = find_column(ALBUM_COLNAMES, cur_cols)
            album_in_curation = True
        except KeyError:
            curation_album_col = None
            album_in_curation = False

        # Canonical columns
        print('🧼 Cleaning track, artist, and album names in curation...')
        curation['track'] = curation[curation_track_col]
        curation['artist'] = curation[curation_artist_col]
        curation['album'] = curation[curation_album_col] if album_in_curation else ''
        curation['clean_track'] = curation['track'].apply(lambda x: clean_text(x, args.trim_aggressive))
        curation['clean_artist'] = curation['artist'].apply(lambda x: clean_text(x, args.trim_aggressive))
        curation['clean_album'] = curation['album'].apply(lambda x: clean_text(x, args.trim_aggressive)) if album_in_curation else ''

        print('🔁 Matching tracks...')
        start_time = time.time()
        matched = []
        not_found = []

        def process_row(row):
            res = match_row(
                row,
                library_keys,
                library_album_keys,
                artist_buckets,
                first_token_buckets,
                album_in_curation,
                args.min_score,
                args.title_weight,
                args.artist_weight,
                args.ngram_weight,
                args.album_weight,
                args.trim_aggressive,
            )
            return res if res else row

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_row, row._asdict() if hasattr(row, '_asdict') else row): idx for idx, row in curation.iterrows()}
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                if isinstance(result, dict) and result.get('match_type'):
                    matched.append(result)
                else:
                    # ensure we push a dict with the raw row if no match
                    if not isinstance(result, dict):
                        result = result.to_dict() if hasattr(result, 'to_dict') else dict(result)
                    not_found.append(result)

                if i % 100 == 0 or i == len(curation):
                    elapsed = time.time() - start_time
                    avg_time = elapsed / max(i, 1)
                    eta = avg_time * (len(curation) - i)
                    percent = (i / max(len(curation), 1)) * 100
                    print(f"[INFO] Processed {i}/{len(curation)} ({percent:.1f}%). Elapsed: {elapsed/60:.1f} min. ETA: {eta/60:.1f} min.")

        print(f"✅ Matched: {len(matched)} | ❌ Not found: {len(not_found)}")

        # Save outputs with consistent column order
        base = os.path.splitext(os.path.basename(curation_path))[0]
        matched_file = f"{base}_matched_v2.csv"
        not_found_file = f"{base}_not_found_v2.csv"
        print('💾 Saving results...')

        matched_cols = [
            'track', 'artist', 'album',
            'matched_track', 'matched_artist', 'matched_album', 'mediaid',
            'ratio_title', 'ratio_artist', 'ratio_album',
            'ngram_title', 'ngram_artist', 'ngram_album', 'match_type'
        ]

        # Ensure columns exist even if lists are empty
        def ensure_cols(df, cols):
            for c in cols:
                if c not in df.columns:
                    df[c] = ''
            return df[cols]

        pd.DataFrame(matched, copy=False).pipe(ensure_cols, matched_cols).to_csv(matched_file, index=False)
        pd.DataFrame(not_found, copy=False)[['track', 'artist', 'album']].to_csv(not_found_file, index=False)

        print(f"✅ Done. Output files for {curation_path}:")
        print(f" - {matched_file}")
        print(f" - {not_found_file}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('❌ Error during matching:', e)
        sys.exit(1)
