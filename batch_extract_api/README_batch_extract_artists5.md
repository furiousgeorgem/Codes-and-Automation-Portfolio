Role: Lead Data Engineer

Tech Stack: Python, Pandas, FuzzyWuzzy/Levenshtein, Caffeinate

Executive Summary Developed a high-performance reconciliation engine to synchronize the SXM/Pandora music catalog. This script serves as the primary processing layer, utilizing advanced fuzzy matching algorithms to automate the reconciliation of the majority of the catalog where metadata is inconsistent but mathematically similar.

The Challenge Music metadata across different platforms often contains disparate naming conventions, varied character encoding, and minor typos. Standard exact-match queries fail to link these assets, creating a massive manual bottleneck in the catalog synchronization pipeline.

The Solution * High-Confidence Matching: Implemented fuzzy string matching to identify and link tracks with minor metadata discrepancies (e.g., typos or formatting variations).

Threshold-Based Automation: Developed a scoring system that automatically approves high-confidence matches, processing the vast majority of the catalog without human intervention.

Triage for AI Review: Engineered the script to identify "Low Confidence" results—cases where strings are too ambiguous for fuzzy logic—and export them specifically for the AI_Match3 reasoning layer.

System Persistence: Integrated caffeinate to prevent system sleep during high-volume batch processing, ensuring 100% completion of large datasets.