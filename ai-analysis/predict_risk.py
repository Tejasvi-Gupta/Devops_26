"""
A simple predictive model: given a student's check-run history so far,
estimate the probability their environment setup will end up with
unresolved (missing/outdated) requirements.

This is intentionally simple -- logistic regression on a handful of
hand-built features -- because the goal for v1 is a working, explainable
baseline, not a sophisticated model. With more data (more students, more
check runs over time), this can be swapped for something richer without
changing how it's called.

Usage:
    python predict_risk.py --data data.csv
"""
import argparse
import sys

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (student, check_run): aggregate features describing that
    check run, plus the label we're trying to predict (whether ANY
    requirement in that run ended up unresolved).
    """
    grouped = df.groupby(["student_id", "student_name", "check_run_id"])

    features = grouped.agg(
        triggered_at=("triggered_at", "first"),
        total_requirements=("status", "size"),
        num_missing=("status", lambda s: (s == "missing").sum()),
        num_outdated=("status", lambda s: (s == "outdated").sum()),
        num_satisfied=("status", lambda s: (s == "satisfied").sum()),
        num_skipped=("action_taken", lambda s: (s == "skipped_by_student").sum()),
    ).reset_index()

    features["unresolved_fraction"] = (
        features["num_missing"] + features["num_outdated"]
    ) / features["total_requirements"]

    # Label: 1 if this check run ended with at least one unresolved
    # requirement, 0 if fully satisfied.
    features["at_risk"] = (features["unresolved_fraction"] > 0).astype(int)

    return features


def train_and_evaluate(features: pd.DataFrame) -> dict:
    feature_cols = ["total_requirements", "num_missing", "num_outdated", "num_skipped"]
    X = features[feature_cols]
    y = features["at_risk"]

    if y.nunique() < 2:
        return {
            "trained": False,
            "reason": "All check runs have the same outcome (all at-risk or all "
                      "fully satisfied) -- need more varied data to train a "
                      "meaningful classifier.",
        }

    if len(features) < 10:
        return {
            "trained": False,
            "reason": f"Only {len(features)} check runs available. Need more "
                      f"data (roughly 10+ check runs, ideally across many "
                      f"students) before a trained model is meaningful.",
        }

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression()
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    # Feature importance via coefficients (positive = increases risk)
    importances = dict(zip(feature_cols, model.coef_[0]))

    return {
        "trained": True,
        "accuracy": accuracy,
        "report": report,
        "feature_importances": importances,
        "model": model,
        "scaler": scaler,
        "feature_cols": feature_cols,
    }


def score_current_students(features: pd.DataFrame, result: dict) -> pd.DataFrame:
    """Score every student's MOST RECENT check run with the trained model,
    producing a risk probability -- this is the actionable output an
    instructor would actually look at."""
    if not result["trained"]:
        return pd.DataFrame()

    latest = features.sort_values("triggered_at").groupby("student_id").tail(1)
    X_latest = latest[result["feature_cols"]]
    X_latest_scaled = result["scaler"].transform(X_latest)
    risk_scores = result["model"].predict_proba(X_latest_scaled)[:, 1]

    latest = latest.copy()
    latest["risk_score"] = risk_scores
    return latest[["student_name", "unresolved_fraction", "risk_score"]].sort_values(
        "risk_score", ascending=False
    )


def run(data_path: str) -> int:
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"ERROR: {data_path} not found. Run export_data.py first.", file=sys.stderr)
        return 1

    if df.empty:
        print("ERROR: no data to analyze.", file=sys.stderr)
        return 1

    features = build_features(df)
    print(f"Built {len(features)} check-run-level feature rows from {len(df)} raw result rows.\n")

    result = train_and_evaluate(features)

    if not result["trained"]:
        print(f"Could not train a model: {result['reason']}")
        print("\nShowing raw feature summary instead, for reference:")
        print(features[["student_name", "total_requirements", "num_missing",
                         "num_outdated", "unresolved_fraction"]].to_string(index=False))
        return 0

    print(f"Model accuracy on held-out data: {result['accuracy']:.2f}")
    print("\nClassification report:")
    print(result["report"])

    print("Feature importances (positive = associated with higher risk):")
    for feat, coef in sorted(result["feature_importances"].items(), key=lambda x: -abs(x[1])):
        print(f"  {feat}: {coef:+.3f}")

    print("\nCurrent risk scores per student (based on their latest check run):")
    scores = score_current_students(features, result)
    print(scores.to_string(index=False))

    return 0


def main():
    parser = argparse.ArgumentParser(description="Predict setup risk from check-run data")
    parser.add_argument("--data", default="data.csv")
    args = parser.parse_args()
    sys.exit(run(args.data))


if __name__ == "__main__":
    main()
