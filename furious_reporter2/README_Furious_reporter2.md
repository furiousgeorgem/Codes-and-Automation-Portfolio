Role: Data Operations Engineer

Tech Stack: Python, SQL Export (CSV), Pandas, Slack API (Bot Tokens)

Executive Summary
Engineered a precision reporting tool used to validate and communicate changes in station data following music tagging cycles. The script compares "Pre-Tagging" and "Post-Tagging" SQL exports to calculate the exact delta in song counts and station durations, delivering formatted technical reports directly to the development team via Slack.

The Challenge
In the station-tagging workflow, it is critical to verify that the music tagged for new stations was correctly processed and reflected in the system. Manually cross-referencing SQL exports to find changes across dozens of stations is time-consuming and risks missing data gaps that the development team needs for production tracking.

The Solution
SQL Export Reconciliation: Developed a logic engine to ingest "Before" and "After" snapshots of station data, performing a structural comparison to identify newly added tracks and updated station lengths.

Delta Calculation Engine: Automates the math for song_count and total_hours changes per station, providing a high-fidelity audit trail of the tagging cycle's impact.

Dev-Ready Reporting: Formats the output specifically for the engineering team’s requirements, ensuring the Slack delivery is scannable and ready for immediate technical intake.

Operational Accuracy: By automating the reporting of these deltas, the tool ensures that every station update is accounted for before it moves further down the development pipeline.