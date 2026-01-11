# ADR 0001: Monorepo + Contract-first + Multi-agent Pipeline

## Context
We want a local demo app that is easy to extend and emphasizes trust via validation.

## Decision
- Monorepo with backend (FastAPI) and frontend (React).
- Contract-first design: shared schema mirrored in backend and frontend.
- Pipeline stages are modular; QA gate validates outputs.
- Retry loop is capped; fallback is links-only.

## Consequences
- Faster iteration with stable UI/API shape.
- Easy to add sources, topics, clustering, scheduling later.
- Stronger reliability story for portfolio.
