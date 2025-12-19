Role: AI Architect

Tech Stack: Python, OpenAI API (GPT-4o-mini), JSON Parsing

Executive Summary Developed a sophisticated "Reasoning Layer" designed to resolve the most complex metadata conflicts identified during the primary fuzzy matching pass. This script utilizes Large Language Models (LLMs) to mimic human decision-making for music versioning and artist attribution.

The Challenge Fuzzy matching (V5) is excellent for typos but cannot understand context. It cannot distinguish between a "Studio Version" and a "Remix" if the titles are 90% identical. These "Remix Trap" edge cases previously required thousands of hours of manual human verification.

The Solution * LLM-Driven Contextual Analysis: Leverages GPT-4o-mini to analyze track attributes (Title, Artist, Duration) and determine if two pieces of metadata refer to the exact same recording.

Three-Tiered Classification:

🟢 GREEN: Identity Match (e.g., Remasters).

🟡 YELLOW: Content Substitute (e.g., Radio Edit for Studio).

⚪ NO_MATCH: Rejection (Correctly flags incorrect remixes or live versions).

Structured Data Output: Built the engine to return structured JSON, allowing the results to be instantly injected back into the production database.