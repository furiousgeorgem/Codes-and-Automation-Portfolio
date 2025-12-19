Role: Data Operations Engineer

Tech Stack: Python, Pandas, RapidFuzz, Concurrent.futures (Multi-threading), Regular Expressions

Executive Summary
Developed a high-speed, parallel-processed data reconciliation engine designed to match massive curation datasets against a master music library. The system utilizes a multi-signal scoring algorithm—combining fuzzy string ratios with token-based n-gram analysis—to automate the identification of tracks across inconsistent data sources.

The Challenge
Music curation files often come from different vendors with non-standardized column names and "noisy" metadata (e.g., "Remastered," "Live," or bracketed info). Standard merging techniques fail to handle these variations, and a simple fuzzy search across millions of rows is computationally expensive and slow.

The Solution
Parallel Processing Engine: Implemented ThreadPoolExecutor to leverage multi-core CPU performance, drastically reducing the time required to process large-scale CSV datasets.

Candidate Blocking Strategy: Optimized performance by engineering a "blocking" mechanism. Instead of scanning the whole library for every row, the script buckets candidates by artist and first-token triggers, enabling huge speedups without losing accuracy.

Multi-Signal Weighted Scoring: Built a sophisticated scoring layer that weights four distinct signals:

Ratio/Token Ratios: For character-level similarity.

N-Gram Intersection: For structural word-set similarity.

Album Contribution: Optional weighting when album data is present.

Tail Trimming: A conservative regex engine to strip "Remaster/Live/Radio Edit" noise without losing core track identity.

Adaptive Column Detection: Developed a robust "soft-match" column detector that automatically identifies track, artist, and album headers regardless of the vendor’s naming convention.

Operational Transparency: Integrated real-time progress logging with ETA calculations and confidence-score exports (ratio_title, ngram_artist, etc.), allowing for data-driven triage.