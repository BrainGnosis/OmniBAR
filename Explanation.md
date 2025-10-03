## OmniBAR Reliability Console:
	Feature Walkthrough

This project extends the open-source OmniBAR framework with a full Reliability Console: a frontend dashboard and backend APIs that make benchmarking and observability accessible to both developers and scientists.
The goal is to provide transparent, reproducible insights into how AI agents perform across reliability dimensions (latency, cost, accuracy, completeness, etc.), and to make raw outputs accessible without digging into backend logs.

# Control Room
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

For developers: Latency, cost, and regression metrics are surfaced clearly.
For scientists and non-devs: Raw JSON outputs are accessible without needing to touch the backend.
For teams: Establishes a standardized, transparent workflow for evaluating AI agents at scale.

⚙️ Quickstart
# Clone the repo
git clone https://github.com/AshB4/OmniBAR.git
cd OmniBAR

# Backend setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload

# Frontend setup
cd frontend
npm install

# Run Frontend
npm run dev
Then open: http://localhost:5173

This Reliability Console demonstrates full-stack craftsmanship:
Backend orchestration (FastAPI endpoints, snapshot persistence, health checks).
Frontend polish (React + Zustand + shadcn, responsive dashboards).
User-centric design (JSON Inspector, Judge Feedback, Threshold controls).

It’s designed to help teams measure and compare agent performance with facts. Latency, cost, accuracy, completeness and make those results easy to inspect, share, and act on.

