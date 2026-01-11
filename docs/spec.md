# News Agent Digest — MVP Spec

## Problem
Users want a quick daily digest that is easy to read and based on reputable sources, not misinformation.

## MVP Goal (Demo)
A local web app where a user selects:
- topics (Tech, Finance, Health, Daily, Learning)
- time range (24h / 3d / 7d)
- optional publisher filters

…and gets a citation-backed digest.

## Trust Model (What we can guarantee)
- Sources are restricted to an allowlist of reputable publisher domains.
- Every summary bullet must include at least one citation URL from the allowlist.
- A QA/Validator gate blocks outputs that fail requirements.
- If QA fails after limited retries, return a safe fallback: verified links only.

## Non-Goals (MVP)
- “Guaranteeing truth” beyond reputable sourcing and citation grounding.
- Paywalled full-text extraction at scale.
- User accounts, cloud deployment.

## User Stories
1. As a user, I can select topics and time range and click "Generate Digest".
2. As a user, I can quickly scan cards (headline, publisher, time, bullets).
3. As a user, I can open citations to confirm the summary.
4. As a user, I can see whether a story is multi-source or single-source.

## Pipeline (Conceptual)
Gather → Verify → Summarize → Format → QA Validate → Output
- Retry policy: max 2–3 loops; redo minimal failing stage.

## Output Requirements (Hard Rules)
- Only allowlisted domains
- Each bullet has citations
- No unsupported specifics (names, numbers, dates) without citation support
- Max 3–5 bullets per story
- Clear, readable formatting

## API (Draft)
POST /digest
Request:
- topics: string[]
- range: "24h" | "3d" | "7d"
- publishers?: string[]

Response:
- generated_at
- selected_topics, range
- cards[] with citations and confidence tags
- qa_status: PASS | FAIL | FALLBACK
