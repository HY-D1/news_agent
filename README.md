# News Agent Digest (Local Demo)

A local web app that generates a **citation-backed news digest** by topic and region.

This repo follows a professional, upgrade-friendly workflow:

- contract-first API design (stable request/response schemas),
- modular pipeline structure (future: gather → verify → summarize → QA → format),
- quality gates (lint, typecheck, tests) and CI-ready structure.

> **Day 1 status:** `/digest` returns **mock** data to validate the end-to-end UI↔API contract and dev workflow.  
> Real ingestion + validation pipeline will replace the mock orchestrator in later steps.

---

## Features (current)

- User-friendly local web UI (React + TypeScript)
- Backend API (FastAPI):
  - `GET /health`
  - `POST /digest` (mock digest, schema v1)
- Strict output contract:
  - every bullet includes **at least one citation**
- Code quality:
  - Backend: ruff + mypy + pytest
  - Frontend: ESLint + TypeScript typecheck + build

---

## Trust model (planned)

This project aims to maximize reliability through **process constraints**:

- sources restricted to an **allowlist** of reputable publisher domains (by region),
- every summary bullet is **grounded** with citations,
- a **QA/Validator gate** blocks non-compliant output,
- capped retries with a safe fallback (verified links only).

> Note: no system can guarantee “truth” universally, but this design maximizes trust via reputable sourcing, grounding, and validation.

---

## Architecture overview

### Monorepo

- `backend/` — FastAPI service + pipeline modules
- `frontend/` — React UI

### Pipeline (incremental build)

`backend/app/pipeline/` contains the orchestrator entrypoint (mock today).  
Later stages will be split into separate agents/steps:

gather → verify → summarize → format → QA validate → output (with retry)

### Contracts

- Backend contracts: `backend/app/core/schemas.py`
- Frontend types: `frontend/src/types.ts`

---

## Project structure

```text
news-agent/
  backend/
    app/
      api/            # API routes
      core/           # schemas/contracts
      pipeline/       # orchestrator + pipeline steps (mock today)
      resources/      # sources.yaml (future allowlist config)
      tests/          # pytest tests
    requirements.txt
    requirements-dev.txt
    pytest.ini
  frontend/
    src/
      api.ts          # API client
      types.ts        # shared types (mirrors backend)
      App.tsx         # UI
  .github/workflows/  # CI workflows
  docs/               # spec + ADRs
```

## Run locally

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Verify:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:5173`

Click **Generate** Digest to fetch and render the mock digest.

## API

### `GET /health`

Response:

```json
{ "status": "ok" }
```

### `POST /digest`

Request example:

```json
{
  "topics": ["tech"],
  "range": "24h",
  "regions": ["canada"]
}
```

Response includes:

- `schema_version`
- `generated_at`
- `qa_status`
- `cards[]` (each card has bullets; each bullet has citations)

## Dev quality gates

### Backend

```bash
cd backend
source .venv/bin/activate
ruff check app
mypy app
pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Roadmap (next)

- Gather: RSS ingestion + normalization
- Verify: allowlist enforcement, time window filtering, dedupe, topic tagging
- Summarize: grounded summaries with citations
- QA: validator gate + retry loop + safe fallback
- Later: multi-source clustering, saved preferences, scheduled digests, expanded regions

## License

- MIT