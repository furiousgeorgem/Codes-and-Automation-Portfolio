Role: Data Operations Engineer

Tech Stack: Python, csv module, webbrowser module

Executive Summary
Engineered an automation script to streamline the manual procurement of "Not Found" tracks from the SXM 2025 Q4 library. By automating the browser-level search queries for thousands of metadata pairs, the tool eliminates the "busy work" of manual searching, allowing the team to focus on high-speed catalog acquisition.

The Challenge
When tracks are flagged as "Not Found" in the internal catalog, they must be manually sourced and purchased. Performing individual searches for hundreds of artist/song combinations is a high-friction, repetitive task that consumes hours of operational time and increases the risk of human error during the search process.

The Solution
Batch Search Automation: Developed a Python-driven workflow that parses CSV exports of missing tracks and automatically generates targeted retail search URLs.

Synchronized Browser Integration: Utilizes the webbrowser module to trigger simultaneous search tabs in Chrome, allowing for immediate, one-click verification and acquisition of the required assets.

Low-Friction Procurement: Transformed a tedious, multi-step manual process into a single-click automation, significantly increasing the throughput of the Music Operations team.

Metadata Integrity: Ensures that the exact song title and artist name from the library snapshot are passed directly to the search engine, removing typos that occur during manual entry.