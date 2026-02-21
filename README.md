# News Agent Digest 📰

AI-powered news digest from trusted sources. Select topics and regions, get a personalized summary with verified citations.

![News Agent Screenshot](docs/screenshot.png)

## Quick Start 🚀

### Option 1: One-Command Start (Recommended)

```bash
./start.sh
```

Then open http://localhost:5173

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

---

## Usage

1. **Select Topics** - Click the topics you're interested in (Tech, Finance, Health, etc.)
2. **Select Regions** - Choose news sources by region (Canada, USA, UK, etc.)
3. **Set Time Range** - Last 24 hours, 3 days, or 7 days
4. **Generate** - Click the button and get your personalized digest

### Understanding the Results

- **Multi-source stories** marked with ✓ - verified across multiple publishers
- **Single-source stories** marked with ○ - from one publisher
- **Citations** - Click `[1]`, `[2]` links to view original sources
- **QA Status** - Shows if digest passed quality checks

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 Multi-Source Verification | Stories clustered and cross-referenced across publishers |
| 🔗 Citation-Backed | Every bullet links to original sources |
| ⚡ AI Clustering | Related stories grouped automatically |
| 🌍 Regional Sources | Canada, USA, UK, China, Global news feeds |
| 📱 Responsive UI | Works on desktop and mobile |

---

## Architecture

```
User Request → Gather RSS → Verify/Dedupe → Cluster → Rank → QA Gate → Response
```

- **Backend**: FastAPI + Python
- **Frontend**: React + TypeScript + Vite
- **Pipeline**: Modular stages (gather → verify → cluster → format)

---

## Development

### Backend Commands
```bash
cd backend
pytest                      # Run tests
ruff check app             # Lint
mypy app                   # Type check
```

### Frontend Commands
```bash
cd frontend
npm run lint               # ESLint
npm run typecheck          # TypeScript check
npm run build              # Production build
```

---

## Configuration

Add custom RSS feeds by editing `backend/app/resources/sources.yaml`:

```yaml
regions:
  - region: canada
    publishers:
      - name: Your Publisher
        allowed_domains: ["example.com"]
        feeds:
          - name: Tech News
            url: https://example.com/rss.xml
            topic: tech
```

Available topics: `tech`, `finance`, `health`, `daily`, `learning`  
Available regions: `canada`, `usa`, `uk`, `china`, `global`

---

## API Reference

### Generate Digest
```bash
curl -X POST http://localhost:8000/digest \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["tech", "finance"],
    "range": "24h",
    "regions": ["canada", "usa"]
  }'
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## License

MIT
