"""
Descriptive analytics over exported check-run data (see export_data.py).

Answers questions like:
- Which tools fail most often (missing/outdated)?
- Which students have the most unresolved requirements?
- What's the overall satisfaction rate per environment?

Usage:
    python descriptive_analysis.py --data data.csv
"""
import argparse
import sys

import pandas as pd


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"{path} has no rows")
    return df


def tool_failure_rates(df: pd.DataFrame) -> pd.DataFrame:
    """For each tool, what fraction of check results were NOT satisfied?"""
    summary = (
        df.groupby("tool_name")["status"]
        .apply(lambda s: (s != "satisfied").mean())
        .rename("failure_rate")
        .sort_values(ascending=False)
    )
    counts = df.groupby("tool_name").size().rename("total_checks")
    return pd.concat([summary, counts], axis=1)


def student_struggle_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each student, count how many of their MOST RECENT check-run results
    (per environment) are not satisfied. Ranks students by unresolved count,
    descending -- these are the students most likely to need help.
    """
    # Identify each student's most recent check_run per environment, then
    # keep only the result rows belonging to those specific check runs.
    latest_run_ids = (
        df.sort_values("triggered_at")
        .groupby(["student_id", "environment_definition_id"])["check_run_id"]
        .last()
    )
    latest_rows = df[df["check_run_id"].isin(latest_run_ids.values)]

    unresolved = (
        latest_rows[latest_rows["status"] != "satisfied"]
        .groupby(["student_id", "student_name"])
        .size()
        .rename("unresolved_requirements")
        .sort_values(ascending=False)
    )
    return unresolved.reset_index()


def environment_satisfaction_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Overall satisfaction rate per environment, across all check results."""
    summary = (
        df.groupby("environment_name")["status"]
        .apply(lambda s: (s == "satisfied").mean())
        .rename("satisfaction_rate")
        .sort_values()
    )
    return summary.reset_index()


def action_outcome_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """When a requirement wasn't satisfied, what did students actually do?"""
    not_satisfied = df[df["status"] != "satisfied"]
    return (
        not_satisfied.groupby("action_taken")
        .size()
        .rename("count")
        .sort_values(ascending=False)
        .reset_index()
    )


def run_report(data_path: str) -> int:
    try:
        df = load_data(data_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"Loaded {len(df)} check-result rows across {df['student_id'].nunique()} students\n")

    print("=" * 60)
    print("TOOL FAILURE RATES (higher = more often missing/outdated)")
    print("=" * 60)
    print(tool_failure_rates(df).to_string())

    print("\n" + "=" * 60)
    print("STUDENTS RANKED BY UNRESOLVED REQUIREMENTS (latest check per env)")
    print("=" * 60)
    ranking = student_struggle_ranking(df)
    print(ranking.to_string(index=False) if not ranking.empty else "No unresolved requirements -- everyone is compliant.")

    print("\n" + "=" * 60)
    print("ENVIRONMENT SATISFACTION RATE")
    print("=" * 60)
    print(environment_satisfaction_rate(df).to_string(index=False))

    print("\n" + "=" * 60)
    print("WHEN NOT SATISFIED, WHAT DID STUDENTS DO?")
    print("=" * 60)
    print(action_outcome_breakdown(df).to_string(index=False))

    return 0


def main():
    parser = argparse.ArgumentParser(description="Descriptive analytics on check-run data")
    parser.add_argument("--data", default="data.csv")
    args = parser.parse_args()
    sys.exit(run_report(args.data))


if __name__ == "__main__":
    main()
