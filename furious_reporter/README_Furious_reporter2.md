# Station Reporter

Compares pre/post curation CSV snapshots and reports changes to Slack. Built for QA validation in music station tagging workflows.

## What It Does

- Compares two CSV files (before and after curation)
- Identifies added, removed, and modified tracks
- Calculates delta statistics
- Sends formatted report to Slack channel
- Generates local text report

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

Create a `requirements.txt` file:

```
pandas>=2.0.0
requests>=2.31.0
```

**Python version:** 3.8+

## Usage

### Basic Usage

```bash
python furious_reporter3.py before.csv after.csv
```

### With Slack Integration

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
python furious_reporter3.py before_curation.csv after_curation.csv
```

## Input Format

CSV files should contain track identifiers. The script auto-detects ID columns.

**Supported ID column names:**
- `id`, `track_id`, `mediaid`, `song_id`

**Example before.csv:**

```csv
id,track,artist,album
123,Hotel California,Eagles,Hotel California
456,Bohemian Rhapsody,Queen,A Night at the Opera
789,Stairway to Heaven,Led Zeppelin,Led Zeppelin IV
```

**Example after.csv:**

```csv
id,track,artist,album
123,Hotel California,Eagles,Hotel California
456,Bohemian Rhapsody,Queen,A Night at the Opera
999,Imagine,John Lennon,Imagine
```

## Output

### Console Output

```
Station Curation Report
=======================

Before: 3 tracks
After: 3 tracks

Changes:
✓ Added: 1 tracks
✗ Removed: 1 tracks
→ Net change: 0 tracks

Details:
- Added IDs: 999
- Removed IDs: 789
```

### Slack Message

Formatted Slack message with emoji indicators:

```
📊 Station Curation Report

📁 Before: 3 tracks
📁 After: 3 tracks

📈 Changes:
✅ Added: 1 tracks
❌ Removed: 1 tracks
➡️ Net change: 0 tracks

🔍 Details:
Added: 999
Removed: 789
```

### Local Report File

Generates `curation_report_[timestamp].txt` with full details.

## How It Works

1. **Load CSVs**: Uses pandas to read both files
2. **Auto-detect ID column**: Tries common ID column names
3. **Calculate delta**: Uses set operations to find added/removed IDs
4. **Generate report**: Formats statistics and changes
5. **Send to Slack**: Posts via webhook (if configured)
6. **Save locally**: Writes timestamped text file

## Configuration

### Slack Webhook Setup

1. Create incoming webhook in your Slack workspace
2. Set environment variable:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
```

Or add to your `.bashrc` / `.zshrc` for persistence.

### Without Slack

The script works without Slack configuration—it will just skip the Slack notification and only generate console/file output.

## Example Workflow

### Station Tagging QA Process

1. **Export current station playlist**: `station_before.csv`
2. **Curator makes changes** (adds/removes tracks)
3. **Export updated playlist**: `station_after.csv`
4. **Run reporter**:

```bash
python furious_reporter3.py station_before.csv station_after.csv
```

5. **Review changes** in Slack channel
6. **Verify** removals were intentional

## Example Output (Full)

```bash
$ python furious_reporter3.py before.csv after.csv

Loading files...
✓ Loaded before.csv: 1,250 tracks
✓ Loaded after.csv: 1,248 tracks

Analyzing changes...

Station Curation Report
=======================

Before: 1,250 tracks
After: 1,248 tracks

Changes:
✓ Added: 15 tracks
✗ Removed: 17 tracks
→ Net change: -2 tracks

Details:
Added IDs: 10001, 10002, 10003, 10004, 10005...
Removed IDs: 5001, 5002, 5003, 5004, 5005...

✓ Report saved: curation_report_20250101_143022.txt
✓ Posted to Slack: #station-updates
```

## Use Case

Built for music curation teams who need to track and validate changes to station playlists. Automates change detection and team notification, replacing manual playlist comparisons.

**Workflow scenarios:**
- Station curation QA (verify intended changes)
- Automated change logs for compliance
- Team notifications of playlist updates
- Audit trail for editorial decisions

## Technical Details

**Key features:**
- Pandas for efficient CSV handling
- Auto column detection with fallback logic
- Set-based delta calculation (O(n) complexity)
- Slack webhook integration
- Timestamped local reports
- Error handling for missing columns/files

**Column detection priority:**
1. `id`
2. `track_id`
3. `mediaid`
4. `song_id`

Falls back to first column if none found.

**Performance:**
- Handles playlists of 100,000+ tracks
- Delta calculation is near-instant (set operations)
- Network delay only for Slack posting (~1 second)

## Notes

- Track IDs must be unique within each file
- Script assumes ID column contains integers or strings
- Slack webhook URL should never be committed to version control
- Reports are timestamped to prevent overwriting
- Works with any CSV format that has an ID column

## Error Handling

**Missing ID column:**
```
Error: Could not find ID column in before.csv
Tried: id, track_id, mediaid, song_id
```

**Invalid Slack webhook:**
```
Warning: Failed to post to Slack (check webhook URL)
Report saved locally: curation_report_20250101_143022.txt
```

## Limitations

- Only tracks additions/removals (not modifications to track metadata)
- Requires unique IDs in both files
- Does not validate track data quality
- Slack integration requires webhook setup
