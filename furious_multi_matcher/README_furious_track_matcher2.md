# Fuzzy Multi-Matcher

High-speed parallel track matching engine that reconciles music catalogs with inconsistent metadata. Uses fuzzy string matching and weighted scoring to handle typos, variations, and formatting differences.

## What It Does

Compares two CSV files of music tracks and finds matches even when:
- Titles have typos or variations ("feat." vs "featuring")
- Artist names are formatted differently ("The Beatles" vs "Beatles")
- Extra metadata like "(Remastered)" or "[Radio Edit]" is present
- Tracks appear in different orders

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

Create a `requirements.txt` file:

```
pandas>=2.0.0
rapidfuzz>=3.0.0
```

**Python version:** 3.8+

## Usage

### Basic Usage

```bash
python furious_multi_matcher4.py source.csv reference.csv
```

### Example

```bash
python furious_multi_matcher4.py playlist_to_match.csv master_catalog.csv
```

## Input Format

Both CSV files should contain track and artist columns. The script auto-detects column names.

**Supported column names:**
- Track: `track`, `song`, `title`, `name`
- Artist: `artist`, `artists`, `performer`

**Example source.csv:**

```csv
track,artist
Hotel California,Eagles
Bohemian Rhapsody,Queen
```

**Example reference.csv:**

```csv
song,artists,album
Hotel California (Remastered),The Eagles,Hotel California
Bohemian Rhapsody,Queen,A Night at the Opera
```

## Output Files

The script generates three output files:

### 1. `matched_tracks.csv`
High-confidence matches with match scores.

```csv
source_track,source_artist,matched_track,matched_artist,match_score
Hotel California,Eagles,Hotel California (Remastered),The Eagles,0.95
```

### 2. `not_found_tracks.csv`
Tracks with no confident match (score < 0.85).

```csv
source_track,source_artist
Obscure B-Side,Unknown Artist
```

### 3. `match_stats.txt`
Summary statistics:
- Total tracks processed
- Matched count
- Not found count
- Match rate percentage
- Processing time

## How It Works

### Matching Algorithm

1. **Candidate Blocking**: For each source track, find potential matches by filtering reference tracks with similar artist names
2. **Fuzzy Scoring**: Calculate similarity scores using:
   - Character-level similarity (Levenshtein distance)
   - N-gram overlap (word-level matching)
   - Duration comparison (if available)
3. **Weighted Score**: Combine metrics with weights favoring title match over artist match
4. **Threshold Filter**: Accept matches with score ≥ 0.85 (configurable)

### Scoring Breakdown

```
Total Score = (0.6 × title_score) + (0.4 × artist_score)

Where:
- title_score = max(character_similarity, ngram_similarity)
- artist_score = max(character_similarity, ngram_similarity)
```

### Performance Features

- **Multi-threaded**: Uses ThreadPoolExecutor for parallel processing
- **Intelligent blocking**: Reduces O(n²) comparisons by filtering candidates
- **Progress tracking**: Shows real-time progress and ETA
- **Memory efficient**: Processes in chunks for large datasets

## Configuration

Edit these constants in the script to tune matching behavior:

```python
MATCH_THRESHOLD = 0.85      # Minimum score for confident match
CANDIDATE_THRESHOLD = 0.70  # Minimum artist similarity for candidates
MAX_CANDIDATES = 50         # Maximum candidates to score per track
NUM_WORKERS = 4             # Parallel worker threads
```

## Example Output

```bash
$ python furious_multi_matcher4.py playlist.csv catalog.csv

Loading source file: playlist.csv (1,250 tracks)
Loading reference file: catalog.csv (45,000 tracks)

Processing tracks...
[████████████████████] 100% | 1250/1250 | ETA: 0s

Results:
✓ Matched: 1,180 tracks (94.4%)
✗ Not found: 70 tracks (5.6%)
⏱ Processing time: 45.2 seconds

Output files created:
- matched_tracks.csv
- not_found_tracks.csv
- match_stats.txt
```

## Use Case

Built for reconciling music catalogs across different vendors, labels, or platforms where track metadata is inconsistent. Handles millions of comparisons efficiently using parallel processing and smart candidate blocking.

**Common scenarios:**
- Matching internal playlist against streaming service catalog
- Cross-referencing label submissions with existing library
- Deduplicating merged databases with different naming conventions
- QA validation of track imports

## Technical Details

**Fuzzy matching techniques:**
- **RapidFuzz**: Fast Levenshtein distance calculations
- **N-gram analysis**: Word-level similarity for multi-word titles
- **Candidate blocking**: Artist pre-filter reduces search space
- **Parallel processing**: ThreadPoolExecutor for CPU-bound scoring

**Text normalization:**
- Removes parentheticals like "(Remastered)", "[Radio Edit]"
- Strips "feat.", "ft.", "featuring" variations
- Converts to lowercase
- Removes special characters

**Performance:**
- Processes ~30-50 tracks/second on typical hardware
- Scales linearly with additional CPU cores
- Handles datasets of 100,000+ tracks

## Notes

- Match threshold of 0.85 balances precision vs. recall (tune based on your needs)
- Artist blocking prevents mismatches across unrelated artists
- Review `not_found_tracks.csv` for tracks that may need manual verification
- For very large datasets (>100k tracks), consider increasing `NUM_WORKERS`

## Limitations

- Does not handle remix/live version detection (all versions treated equally)
- Duration matching requires both files to have duration data
- Performance degrades if candidate blocking fails (uncommon artist names)
