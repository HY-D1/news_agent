# MVP Acceptance Criteria

## Functional
- UI lets user select topics + time range and generates a digest.
- Results are displayed as readable cards with citations.
- Clicking a citation opens the original article.

## Trust / Validation
- Only allowlisted publisher domains appear in results.
- Every bullet has at least one citation.
- QA gate blocks non-compliant output and triggers limited retries.
- If still failing, return verified links-only fallback.

## Engineering
- Strict JSON schema for request/response.
- Repo structured to add new pipeline steps/tools without rewrites.
- CI runs lint/typecheck/tests (added later in Day 1).

## Day 3: Dynamic Orchestration & Quality
- **Topic tagging**: Articles are correctly mapped to requested topics; `max_cards_per_topic` is respected.
- **Clustering/Dedupe**: Multiple publishers covering the same story are grouped into one card; `MULTI_SOURCE` confidence tag is applied when >= 2 publishers are clustered.
- **Ranking**: Cards are ranked by confidence (multi-source first) and then by recency.
- **QA validation**: Every card passes a gate checking for allowlisted domains and 100% citation coverage for bullets.
- **API Integrity**: No changes made to `backend/app/core/schemas.py` or `frontend/src/types.ts`.

