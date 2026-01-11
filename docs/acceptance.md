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
