# AI Analysis

Standalone scripts that analyze accumulated check-run data from the
backend: descriptive stats first, a simple predictive model on top.
This is v1 scope by design — no new service, no scheduled jobs, just
scripts you run against a fresh export whenever you want a read on the
data. See `backend/README.md`'s "Remaining Work" section for how this
could later become an API endpoint.

## What's here

- `export_data.py` — pulls data from the backend's API (students,
  environment definitions, check runs) and flattens it into `data.csv`
  (one row per student/requirement/check-run)
- `descriptive_analysis.py` — aggregate stats: tool failure rates, which
  students have the most unresolved requirements, environment-wide
  satisfaction rate, what students do when something's missing
- `predict_risk.py` — a logistic regression model that scores each
  student's *current* risk of ending up with unresolved requirements,
  based on features of their check-run history

## Setup

```
cd ai-analysis
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Usage

**1. Make sure the backend is running** and has real check-run data (run
the Student Agent at least a few times across a few students/environments
— the more data, the more meaningful the analysis).

**2. Export the data:**
```
python export_data.py --backend-url http://127.0.0.1:8000 --out data.csv
```

**3. Run descriptive analytics:**
```
python descriptive_analysis.py --data data.csv
```

**4. Run the predictive model:**
```
python predict_risk.py --data data.csv
```

## What was verified

Seeded 15 students with three distinct patterns (fully compliant, chronically
struggling, improving over two check-runs — 100 check-result rows total),
exported them through the real API, and ran both analysis scripts:

- **Descriptive analysis** correctly identified the 5 struggling students by
  name, correctly showed Python/Node with higher failure rates than
  Git/Docker (matching the seeded pattern), and correctly excluded the
  "improving" students from the unresolved ranking once they'd resolved.
- **Predictive model** trained cleanly (100% held-out accuracy, though note
  this reflects how cleanly separated the *seeded* synthetic patterns were
  — real-world data will be noisier), and correctly ranked the struggling
  students as highest-risk (~0.92) vs. compliant students (~0.11).

One real bug was found and fixed during testing: the "current risk per
student" step was picking each student's latest row by sorting on
`check_run_id` (a random UUID) instead of `triggered_at` (the actual
timestamp) — meaning it could score a student's *older* check-run instead
of their most recent one. Confirmed fixed by re-testing against two
students whose compliance state changed between their first and second
check-run.

## Model caveats (read before trusting this on real data)

- **Small-data guardrail**: `predict_risk.py` refuses to train (and tells
  you why) if there are fewer than ~10 check-run rows, or if every check
  run has the same outcome. This is intentional — a model "trained" on too
  little or too homogeneous data would produce confident-looking nonsense.
- **The 100% accuracy above is a property of the synthetic test data**,
  which was seeded with clearly separable patterns to prove the pipeline
  works end-to-end. Real student data will be messier; expect (and trust)
  lower, more realistic accuracy once this runs against real usage.
- This is a baseline model (4 simple features, logistic regression) by
  design — the goal was an honest, explainable v1, not a sophisticated
  one. See "Extending this later" below.

## Extending this later

- **Turn into an API endpoint**: wrap `export_data` + `predict_risk`'s
  logic into a `GET /environment-definitions/{id}/risk-report` route on
  the backend, so the frontend can show risk scores in the instructor
  dashboard instead of requiring a manual script run.
- **Richer features**: time between check-runs, which specific tools
  each student struggles with, whether they've used `--dry-run` a lot
  (hesitation signal), enrollment-to-first-check-run latency.
- **Better model**: once there's enough real data, compare against a
  random forest or gradient boosting model — but only after confirming
  the extra complexity earns its keep over this baseline.
