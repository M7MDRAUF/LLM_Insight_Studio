# LLM Insight Studio

> **Research-grade NLP model comparison platform** — upload datasets, run multi-task evaluations across Hugging Face models, compare results side-by-side, and generate AI-written research reports with provenance.

**Repo:** https://github.com/M7MDRAUF/LLM_Insight_Studio

```bash
git clone https://github.com/M7MDRAUF/LLM_Insight_Studio.git
cd LLM_Insight_Studio
```

---

## Professor Verification Screenshots

The following screenshots were captured from a local run of LLM Insight Studio
using the FastAPI backend (`http://127.0.0.1:8000`) and the Next.js frontend
(`http://localhost:3000`). They document the main pages and workflows
requested for verification, including dataset upload, the experiment wizard
and lifecycle, metric cards, research-report generation, the markdown report
viewer, and the side-by-side compare view.

| #   | Area                                  | Screenshot                                                               |
| --- | ------------------------------------- | ------------------------------------------------------------------------ |
| 01  | Home / Overview                       | [Open screenshot](screenshots/01-home-overview.png)                      |
| 02  | API Docs (Swagger UI)                 | [Open screenshot](screenshots/02-api-docs.png)                           |
| 02b | API health (`/health/live`)           | [Open screenshot](screenshots/02b-api-health-live.png)                   |
| 03  | Datasets page                         | [Open screenshot](screenshots/03-datasets-page.png)                      |
| 04  | Dataset upload form                   | [Open screenshot](screenshots/04-dataset-upload-form.png)                |
| 05  | Dataset upload success                | [Open screenshot](screenshots/05-dataset-upload-success.png)             |
| 06  | Experiment wizard — dataset selected  | [Open screenshot](screenshots/06-experiment-wizard-dataset-selected.png) |
| 07  | Experiment wizard — task lanes        | [Open screenshot](screenshots/07-experiment-wizard-task-lanes.png)       |
| 08  | Experiment wizard — advanced options  | [Open screenshot](screenshots/08-experiment-wizard-advanced-options.png) |
| 09  | Experiment lifecycle (queued/running) | [Open screenshot](screenshots/09-experiment-running.png)                 |
| 10  | Experiment completed + metric cards   | [Open screenshot](screenshots/10-experiment-completed-metrics.png)       |
| 11  | Research report generation            | [Open screenshot](screenshots/11-report-generation.png)                  |
| 12  | Markdown report viewer (provenance)   | [Open screenshot](screenshots/12-report-viewer.png)                      |
| 13  | Compare page (side-by-side metrics)   | [Open screenshot](screenshots/13-compare-page.png)                       |
| 14  | Settings page                         | [Open screenshot](screenshots/14-settings-page.png)                      |

> All screenshots above are real captures of the running application using the
> default `mock` inference provider. No images were generated, edited, or
> staged.

---

## Architecture

```
ai520_WA/
├── apps/
│   ├── api/          # FastAPI backend (Python 3.11+)
│   └── web/          # Next.js 14 App Router frontend (TypeScript)
├── services/         # Business logic layer
│   ├── agent/        # AI research report writer (smolagents)
│   ├── artifacts/    # JSON / Markdown I/O
│   ├── data/         # Dataset ingestion (CSV/JSON upload + HF loader)
│   ├── evaluation/   # Classification, QA, Summarisation, Instruct metrics
│   ├── experiments/  # Experiment orchestration + job runner
│   └── ml/           # Inference provider abstraction (mock + transformers)
├── tests/            # pytest integration + unit tests
├── artifacts/        # SQLite DB + experiment/report artifacts (gitignored)
└── docs/
    └── MASTER_SPEC.md
```

**Key design patterns:** `routers → services → providers/repositories`, Pydantic v2 contracts throughout, SQLModel ORM, provider abstraction (`InferenceProvider`) with `mock` and `transformers` backends.

---

## Features

| Feature                                            | Status                                            |
| -------------------------------------------------- | ------------------------------------------------- |
| CSV / JSON dataset upload                          | ✅                                                |
| Hugging Face dataset import                        | ✅ (requires `pip install -e ".[ml]"`)            |
| Experiment wizard (4 task lanes)                   | ✅ Classification · Summarisation · QA · Instruct |
| Background job runner with heartbeat watchdog      | ✅                                                |
| Experiment cancellation                            | ✅                                                |
| Side-by-side metric comparison table               | ✅                                                |
| AI research report generation                      | ✅ 13+ provenance references                      |
| Markdown report viewer                             | ✅                                                |
| Prometheus-style `/metrics` endpoint               | ✅                                                |
| Mock inference provider (zero-dependency dev mode) | ✅                                                |

---

## Prerequisites

| Tool    | Version                |
| ------- | ---------------------- |
| Python  | ≥ 3.11                 |
| Node.js | ≥ 18 (20+ recommended) |
| npm     | ≥ 9                    |
| Git     | any modern             |

---

## Quick Start

### 1. Clone & install backend

```bash
# From repo root
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e .
```

### 2. Start the API

```bash
# Uses mock inference provider by default (no GPU required)
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: http://localhost:8000/docs

### 3. Start the frontend (separate terminal)

```bash
cd apps/web
npm install
# Point the web UI at the local API
# PowerShell:
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000/api/v1"
# bash/zsh:
export NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000/api/v1"

npm run dev
```

App: http://localhost:3000

---

## First-time walkthrough (5 minutes)

1. **Open** http://localhost:3000.
2. Click **Datasets** → **Upload a file** → select any CSV with at least one text column (e.g. `text,label`). Fill `text_columns=text` and `label_columns=label`, then **Upload**. The new dataset appears under _Imported datasets_.
3. Click **Use →** next to your dataset. The wizard opens with the dataset preselected.
4. Pick one or more **Task lanes** (`classification`, `summarization`, `qa`, `instruct`).
5. (Optional) Expand **Advanced options** to tweak `temperature`, `top_p`, `max_new_tokens`, `batch_size`, or toggle the post-run report.
6. Click **Start experiment** — you are redirected to the experiment detail page. The timeline transitions `queued → running → completed` and metric cards appear.
7. Click **Generate research report** — a markdown report with 13+ provenance references is produced. Open the link to view it.
8. Visit **Compare** to select multiple completed runs and view metrics side-by-side.

The default `mock` provider is deterministic and runs in milliseconds — no GPU required.

---

## Environment Variables

Create a `.env` file at the repo root to override defaults:

| Variable                   | Default                 | Description                                                                                      |
| -------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------ |
| `INFERENCE_PROVIDER`       | `mock`                  | `mock` (no-GPU) or `transformers` (real HF models)                                               |
| `HF_TOKEN`                 | —                       | HuggingFace token for private model/dataset access                                               |
| `WEB_ORIGIN`               | `http://localhost:3000` | CORS allowed origin                                                                              |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | API base URL for the web UI (**required in production** — `next build` will fail-fast otherwise) |
| `EXPERIMENT_TIMEOUT_S`     | `300`                   | Max seconds before an experiment run is timed out                                                |

> **Tip:** the experiment wizard exposes an **Advanced options** section
> (collapsed by default) that lets you tune generation parameters
> (`temperature`, `top_p`, `max_new_tokens`, `batch_size`) and the post-run
> report toggles (`report.enabled`, `report.include_references`). When
> `report.enabled=false`, calls to `POST /agent/report` for that experiment
> are rejected with a typed error so the choice is honored end-to-end.

---

## ML Stack (optional)

For real Hugging Face inference, install the optional ML extras:

```bash
pip install -e ".[ml]"
# Then set INFERENCE_PROVIDER=transformers in .env
```

Required packages: `transformers`, `datasets`, `evaluate`, `scikit-learn`, `rouge-score`, `numpy`, `pandas`.

---

## Testing

### Backend (pytest)

```bash
# From repo root, with venv active
python -m pytest -q
# Expected: 41 passed
```

### Static analysis

```bash
ruff check .
python -m mypy apps services
bandit -r apps services -q
python -m vulture apps services --min-confidence 80
```

### Frontend (vitest)

```bash
cd apps/web
npm run test
# Expected: 31 passed
```

### E2E (Playwright)

```bash
cd apps/web
npx playwright test
# Requires both servers running on :8000 and :3000
```

---

## Project Structure (detailed)

```
apps/api/
  main.py              # FastAPI app factory, middleware, router registration
  core/
    db.py              # SQLite engine + session factory
    settings.py        # Pydantic-settings config (env vars)
    errors.py          # Typed API error hierarchy
    deps.py            # FastAPI dependency injection
  routers/
    experiments.py     # CRUD + run + cancel + status polling
    datasets.py        # Upload (CSV/JSON) + HF import
    agent.py           # Report generation trigger
    compare.py         # Side-by-side metric aggregation
    reports.py         # Report retrieval
    artifacts.py       # Raw artifact download
    health.py          # /health + /metrics
  repositories/
    experiments.py     # SQLModel experiment CRUD
    datasets.py        # Dataset manifest CRUD
    models.py          # ORM row definitions
  schemas/             # Pydantic request/response schemas

apps/web/
  app/                 # Next.js App Router pages
    page.tsx           # Overview / home
    datasets/          # Dataset management
    experiments/       # Experiment wizard + detail + status
    compare/           # Side-by-side comparison table
    reports/           # Report viewer (ReactMarkdown + remark-gfm)
    settings/          # Runtime config reference
  components/
    ExperimentWizard.tsx   # react-hook-form + zod validation
    MetricCards.tsx        # Per-task metric display
    ComparisonTable.tsx    # Multi-experiment comparison
    ReportViewer.tsx       # Markdown renderer
    DatasetPicker.tsx      # Dataset selection control
    RunStatusTimeline.tsx  # Experiment lifecycle timeline
    UploadDropzone.tsx     # File upload UI
  lib/
    api.ts             # Type-safe fetch wrappers
    query-provider.tsx # TanStack Query setup
```

---

## Troubleshooting

| Symptom                                                 | Fix                                                                                                                                           |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm error Missing script: "dev"`                       | You ran `npm run dev` from the repo root. Run it from `apps/web/` instead.                                                                    |
| Frontend shows _Unable to reach the API_                | Check `NEXT_PUBLIC_API_BASE_URL` is set to `http://127.0.0.1:8000/api/v1` and the API is up at `/api/v1/health/live`.                         |
| `Need to install the following packages: next@16`       | The `cd` into `apps/web` did not happen — `next` is a local dep, not global. `cd` first, then run npm.                                        |
| CORS error in browser console                           | The API only allows `http://localhost:3000` and `http://127.0.0.1:3000` by default. Set `WEB_ORIGIN` if you serve the UI from another origin. |
| Classification accuracy is `0.0` with the mock provider | Expected — mock returns `POSITIVE`/`NEGATIVE` regardless of your label space. Use real labels in `transformers` mode for meaningful scores.   |
| Experiment stuck in `queued`                            | Check the API terminal for tracebacks. The job runner logs `experiment_failed` with the cause.                                                |

---

## License

MIT
