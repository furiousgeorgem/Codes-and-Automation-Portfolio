Codes and Automation Portfolio
George Sayama McHenry | Data Operations & Technical Curation GitHub: furiousgeorgem

Executive Summary
A specialized collection of Python-driven automation tools designed for high-volume music data curation, catalog synchronization, and operational reporting. This portfolio demonstrates the ability to bridge the gap between complex music metadata and scalable engineering solutions, specifically tailored for the needs of major media agencies and streaming platforms.
Core Competencies
Automation & Scripting: Streamlining manual bottlenecks in music procurement and tagging.

Data Reconciliation: High-speed fuzzy matching and AI-driven metadata verification.

Engineering Reporting: Automating SQL delta reports and developer-handoff notifications.

Workflow Optimization: Transforming tedious manual searches into synchronized browser automations.
| Project | Focus | Tech Stack |
| :--- | :--- | :--- |
| **[Batch Extract API](./batch_extract_api/)** | Multi-tier catalog reconciliation (Fuzzy + AI) | Python, OpenAI API, RapidFuzz |
| **[Furious Multi-Matcher V2](./furious_multi_matcher2/)** | High-speed parallel matching engine | Multi-threading, N-Grams, Regex |
| **[Station Tagging Reporter](./furious_reporter2/)** | SQL Export Delta & Slack Integration | Pandas, Slack API, SQL Logic |
| **[Amazon Search Automator](./amazon_songs/)** | Browser-level procurement automation | Python, `webbrowser` |

Repository Structure

├── amazon_songs/                 # Procurement automation
├── batch_extract_api/            # Tiered Fuzzy & AI matching documentation
├── furious_multi_matcher2/       # Parallelized matching engine
├── furious_reporter2/            # SQL Delta/Slack reporting
├── WORKFLOW.md                   # Operational standards
└── README.md                     # Portfolio directory
Operational ExcellenceBeyond the code, this repository showcases a "Low-Friction" mindset. Every tool here was built to solve a specific operational pain point:Removing Manual Work: Shifting from one-by-one searching to automated batching.Ensuring Data Integrity: Using weighted scoring to prevent "Remix Traps" and metadata drift.Cross-Functional Communication: Automating technical updates for dev teams to ensure project transparency.

## **Portfolio Review Guide**

This repository is designed for technical review by hiring managers and engineering teams. To evaluate the logic and code quality:

1. **Explore Project Folders:** Each directory represents a standalone operational solution.
2. **Review the Logic:** Open the `.py` files to examine the implementation of multi-threading, fuzzy matching, and API integrations.
3. **Analyze the Documentation:** Each project includes a dedicated Markdown file explaining the "Problem/Solution" framework and the business impact of the tool.

*Note: This code is provided for demonstration of technical proficiency. Proprietary datasets and API credentials have been omitted for security.*