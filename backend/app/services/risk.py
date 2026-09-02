"""
Rule-based setup-risk scores for enrolled students.

This is the API-facing counterpart of ai-analysis/predict_risk.py. The
offline script trains logistic regression when there is enough data; the
endpoint uses an explainable heuristic so a classroom-sized dataset still
produces a useful instructor report instead of refusing to train.
"""
from app.models import CheckRun, CheckResult
from app.models.enums import ActionTaken, CheckResultStatus

HIGH_THRESHOLD = 0.6
MEDIUM_THRESHOLD = 0.3


def _unresolved_count(results: list[CheckResult]) -> tuple[int, int, int]:
    unresolved = 0
    skipped = 0
    for result in results:
        if result.status in (
            CheckResultStatus.MISSING,
            CheckResultStatus.OUTDATED,
            CheckResultStatus.ERROR,
        ):
            unresolved += 1
        if result.action_taken == ActionTaken.SKIPPED_BY_STUDENT:
            skipped += 1
    return unresolved, skipped, len(results)


def score_student(
    latest_run: CheckRun | None,
    previous_run: CheckRun | None,
    requirement_count: int,
) -> tuple[float, str, float | None, list[str]]:
    """
    Returns (risk_score 0-1, risk_level, unresolved_fraction, reasons).
    Never-checked students are scored as highest risk.
    """
    if latest_run is None or not latest_run.results:
        return (
            1.0,
            "high",
            None,
            ["Never submitted a check run"],
        )

    unresolved, skipped, total = _unresolved_count(latest_run.results)
    total = max(total, requirement_count, 1)
    fraction = unresolved / total
    score = fraction
    reasons: list[str] = []

    if unresolved == 0:
        reasons.append("Latest check is fully compliant")
    else:
        reasons.append(f"{unresolved}/{total} requirements unresolved")

    if skipped:
        score = min(1.0, score + 0.1 * skipped)
        reasons.append(f"Skipped {skipped} install prompt(s)")

    if previous_run and previous_run.results:
        prev_unresolved, _, prev_total = _unresolved_count(previous_run.results)
        prev_total = max(prev_total, 1)
        if unresolved / total < prev_unresolved / prev_total:
            score = max(0.0, score - 0.15)
            reasons.append("Improved since previous check")

    if score >= HIGH_THRESHOLD:
        level = "high"
    elif score >= MEDIUM_THRESHOLD:
        level = "medium"
    else:
        level = "low"

    return round(score, 3), level, round(fraction, 3), reasons
