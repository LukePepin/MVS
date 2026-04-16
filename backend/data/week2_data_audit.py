import json
from pathlib import Path
import pandas as pd

BASE = Path("data/baseline_data.csv")
ADV = Path("data/adversarial_balanced_43k.csv")
OUT = Path("week2_data_audit.json")

EXPECTED = ["NodeID","Accel_X","Accel_Y","Accel_Z","Gyro_X","Gyro_Y","Gyro_Z","Timestamp"]

def audit_csv(path: Path):
    df = pd.read_csv(path)

    cols = list(df.columns)
    schema_match = (cols == EXPECTED)
    null_counts = df.isnull().sum().to_dict()

    ts = pd.to_datetime(df["Timestamp"], utc=True, errors="coerce")
    ts_parse_failures = int(ts.isna().sum())

    ts_valid = ts.dropna()
    monotonic = bool(ts_valid.is_monotonic_increasing) if len(ts_valid) > 0 else False

    deltas = ts_valid.diff().dt.total_seconds().dropna()
    gap_stats = {
        "count": int(deltas.shape[0]),
        "mean_s": float(deltas.mean()) if len(deltas) else None,
        "std_s": float(deltas.std()) if len(deltas) else None,
        "min_s": float(deltas.min()) if len(deltas) else None,
        "max_s": float(deltas.max()) if len(deltas) else None,
        "gaps_gt_1s": int((deltas > 1.0).sum()) if len(deltas) else 0,
    }

    return {
        "file": str(path).replace("\\\\", "/"),
        "rows": int(df.shape[0]),
        "columns": cols,
        "schema_match_expected": schema_match,
        "null_counts": {k: int(v) for k, v in null_counts.items()},
        "timestamp_parse_failures": ts_parse_failures,
        "timestamp_monotonic_increasing": monotonic,
        "timestamp_gap_stats_seconds": gap_stats,
    }

def main():
    base = audit_csv(BASE)
    adv = audit_csv(ADV)

    result = {
        "week": "Week 2",
        "expected_schema": EXPECTED,
        "schema_match_between_files": base["columns"] == adv["columns"],
        "datasets": {
            "baseline": base,
            "adversarial_balanced_43k": adv
        }
    }

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote audit report: {OUT}")

if __name__ == "__main__":
    main()