## OmniBAR Reliability Console:
	Feature Walkthrough

This project extends the open-source OmniBAR framework with a full Reliability Console: a frontend dashboard and backend APIs that make benchmarking and observability accessible to both developers and scientists.
The goal is to provide transparent, reproducible insights into how AI agents perform across reliability dimensions (latency, cost, accuracy, completeness, etc.), and to make raw outputs accessible without digging into backend logs.

### Run the Reliability Console Locally

- **Clone & bootstrap**
   ```bash
   git clone https://github.com/AshB4/OmniBAR
   cd OmniBAR
   python3 -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt 
  *or to develop further*
  pip install -e .[dev]
  ```
- **Create secrets**
  ```bash
  cp backend/.env.example backend/.env
  # edit backend/.env and add your OPENAI_API_KEY (keep MOCK_MODE=true for mock runs)
  ```
- **Backend**
  ```bash
  python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
  #Use python -m so it works from any directory and binds to 0.0.0.0, making it accessible if you’re running in Docker or WSL.
  ```

   **For A More  Robust Experince **
  - API docs: Swagger UI at <http://localhost:8000/docs>, ReDoc at <http://localhost:8000/redoc>.
  - Pretty-print JSON responses (e.g., OmniBrew log downloads) with the [JSON Viewer Pro](https://chromewebstore.google.com/detail/json-viewer-pro/eifflpmocdbdmepbjaopkkhbfmdgijcc) browser extension.

- **Frontend**
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- **Browser**
  - Visit <http://localhost:5173>. Start in mock mode to confirm wiring, then switch OmniBrew’s dropdown to live mode once the OpenAI key is set.
  - Start in mock mode to verify wiring.
  - Switch OmniBrew’s dropdown to live mode once your OpenAI key is set.


### Assumptions

- Reviewers have Python 3.10+, Node.js 18+, npm, and can install dependencies from the terminal.
- Local SQLite (for OmniBrew run history) and in-memory lists (for benchmark history) satisfy persistence requirements.
- OpenAI usage stays under the \$10 key limit noted in the brief; live scoring assumes outbound network access and a valid key.
- Execution targets localhost; outbound calls to OpenAI occur only when OmniBrew live mode is enabled.

### Trade-offs

- Focused on core scoring UX—skipped auth, multi-tenancy, and production deployment scripts.
- Accepted SQLite/in-memory storage to avoid database provisioning overhead.
- Synchronous scoring (no background queue) is acceptable for short prompts; long-running suite orchestration was out of scope.
- UI favors clarity over exhaustive accessibility polish; future work would include keyboard trap audits and contrast tuning.

### Architecture Overview

- **Backend (`backend/`)**
  - FastAPI app (`backend/app.py`) exposes Control Room suites, OmniBrew scoring, run history, and a JSON download endpoint for OmniBrew logs.
  - Services (`backend/services/latte_service.py`, `backend/services/scoring.py`) wrap call-and-score behavior plus OmniBAR LLM-judge evaluation.
  - SQLite persistence is handled by SQLAlchemy (`backend/database.py`, `backend/models.py`). Tables are auto-created on startup; no migrations required for the demo scope.
- **Frontend (`frontend/`)**
  - `AppShell` manages navigation and environment badges. Pages map to workflows: Control Room, Benchmarks, Runs, Document Extraction, and OmniBrew.
  - The API layer (`frontend/src/lib/api.ts`) centralizes REST fetches, handles errors, and ensures consistent credential usage.
  - State is held per page via React hooks with shadcn/ui + Tailwind components for quick iteration.
- **Data Flow**
  1. User submits input (suite trigger or OmniBrew form).
  2. Backend calls the LLM (mock/OpenAI), evaluates with OmniBAR, persists the run, and responds with telemetry (latency, tokens, breakdown).
  3. Frontend updates UI panels, charts, and tables.
  4. Users can export the full OmniBrew run log as a CSV for DFL reproducibility straight from the interface.
- **Stack:** FastAPI + SQLAlchemy + SQLite on the backend; React + Vite + shadcn/ui on the frontend, with Tailwind for styling.
- **Error & mode handling:** FastAPI returns structured errors consumed by a shared response handler; OmniBrew surfaces banners when requests fail and falls back to canned data. Mock scoring is forced when `MOCK_MODE=true` (env) or the dropdown selects “Mock,” while live mode requires a valid OpenAI key and handles 401/429 responses by displaying the error message.

### What Was Cut (and why)

- No hosted deployment IaC/scripts—assignment stressed local execution.
- No role-based access control or multi-tenant separation to keep the stack lightweight.
- No async queues for long-running suites; synthetic benchmark payloads keep latency low. Maybe, I'll tackle long running suits in a diffrent version.
- Demo video hosted separately to avoid bloating the repository.

### Tests & Improvement Notes

- Backend: run `pytest` to exercise OmniBAR’s objective suites.
- Frontend: `npm run test:e2e` (after `npx playwright install`) covers key navigation and transparency states.
- Future enhancements: add focused integration tests for OmniBrew submissions and backend smoke tests for live scoring fallbacks.

### AI Assistance

Portions of this project were scaffolded with the help of Codex and ChatGPT to accelerate setup and boilerplate generation. All core logic, scoring integration, and design decisions were implemented and verified manually. This Explanation file was drafted with Codex assistance and reviewed line-by-line before submission.

## UI / UX Design Notes

This project was built with BrainGnosis’ UI principles in mind:
- Modular React components designed for reuse across AgentOS
- Responsive layout with consistent spacing and typography
- Accessible controls (keyboard navigation + ARIA labels)
- Visual feedback for every app state (loading, mock, error, success)
- Emphasis on clarity and performance to make AI workflows intuitive

### Demo & Supporting Assets

- [Demo video (≤5 min) with voiceover](https://www.youtube.com/watch?v=1mEUYETDSjM)
- Improvement notes and reflections: this document plus inline comments track follow-up ideas.

# Page & Feature Guide

## OmniBrew
- **Purpose:** Interactive prompt lab that lets reviewers craft system + user prompts, submit them to OmniBAR, and inspect both the LLM reply and the judge’s scoring output.
- **Modes:** Dropdown toggles between inherited mode, forced mock, and forced live. Live mode invokes OpenAI; mock mode returns deterministic demo strings.
- **Outputs:** Displays assistant reply, barista note, score, latency, and token usage per run. Aggregates rollups for total runs, averages, and per-model stats.
- **Log Export:** “Download log” button generates a JSON snapshot containing every run (including the OmniBAR scoring breakdown) for reproducibility and DFL review.

## Control Room
This is the launchpad for reliability evaluation.
Run Output Benchmarks – Execute curated suites to capture fresh snapshots.
Schedule Reliability Review – Export or automate recurring benchmark reviews.
Reliability Threshold Slider – Set the minimum acceptable score; anything below is treated as failure.
LLM Connectivity Check – Lightweight test to verify the LLM API is reachable and responsive.
Suite Snapshot JSON – One-click access to raw benchmark payloads, with download and copy options.
 Lets engineers launch tests quickly, and gives non-technical stakeholders direct access to structured outputs.

#Benchmarks
 A library of all benchmark results from the latest snapshot.
Summary Cards – Total benchmarks, Passing, Needs Attention.
Benchmark Table – Details per benchmark:
Success Rate, Latency, Cost, Iterations, Updated Timestamp
Status badges show pass/fail at a glance
Raw JSON Inspector – Dropdown to select “All benchmarks” or an individual benchmark, with prettified JSON, syntax highlighting, and copy/download.

Bridges both audiences:
Developers see latency, token cost, iteration counts.
Scientists can grab raw JSON to validate outputs directly.

Runs
The audit log of reliability testing.
Controls:

Clear Run History – Deleat stored runs.

Run LLM Smoke Test – Quick “2+2=4” test to confirm API availability.

Summary Cards:
Total Runs Logged – Count of all historical runs.
Last Run – Suite, status, timestamp, and threshold.
Failures Flagged – Total failed runs in history.

Run History Table:

Suite name, Status, Benchmarks, Successes, Failures, Threshold, Requested At, Snapshot Generated.

 Functions as a regression log. Teams can spot drift, confirm fixes, and maintain an auditable trail of model reliability over time.

# Document Extraction
  A prompt-comparison lab for structured extraction tasks.
Prompt Strategies Sidebar – Switch between iterations (Zero-shot, Few-shot, Tool-augmented, Hybrid).

Iteration Panel: Model, runtime, output length, and four LLM-judge metrics: Content, Structure, Completeness, Accuracy.

Reliability Scores Table: Compare all strategies side-by-side; quickly identify the top performer.
Quality Radar: Visualizes granular strengths (entity recall, line-item accuracy, date normalization, currency handling, layout robustness).
Extracted Sample: Raw JSON payload returned by the agent, with copy/download options.
Failure Drill-down: Lists objectives that fell below threshold.
Judge Feedback: Actionable notes from the evaluator (e.g., regex guard improvements, missing schema tags).

Turns experimentation into evidence. Teams can justify prompt changes with data, see why one strategy beats another, and iterate systematically.

# Runs
- **Audit log:** Tracks every benchmark suite execution (including smoke tests). Displays suite label, successes/failures, thresholds, and timestamps.
- **Actions:** Buttons to clear the stored history and to trigger the LLM smoke test (useful for verifying API connectivity before a full run).
- **Cards:** Quick stats summarizing total runs, last run details, and failures flagged across history.

For developers: Latency, cost, and regression metrics are surfaced clearly.
For scientists and non-devs: Raw JSON outputs are accessible without needing to touch the backend.
For teams: Establishes a standardized, transparent workflow for evaluating AI agents at scale.

This Reliability Console demonstrates full-stack craftsmanship:
Backend orchestration (FastAPI endpoints, snapshot persistence, health checks).
Frontend polish (React + Zustand + shadcn, responsive dashboards).
User-centric design (JSON Inspector, Judge Feedback, Threshold controls).

It’s designed to help teams measure and compare agent performance with facts. Latency, cost, accuracy, completeness and make those results easy to inspect, share, and act on.
