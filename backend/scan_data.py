import pandas as pd
import numpy as np

filepath = r'c:\Users\lukep\Documents\MVS\backend\backend\data\training_data_0001.csv'

def run_scan():
    print(f"Scanning {filepath}...\n")
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"Failed to read CSV: {e}")
        return

    # 1. Verify schema consistency
    expected_cols = ['NodeID', 'Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z', 'Timestamp']
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        print(f"Missing columns: {missing_cols}")
    else:
        print("Schema consistency: OK. All expected columns found.")
    
    # Check for malformed rows / nulls
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print(f"\nFound null values:\n{null_counts[null_counts > 0]}")
    else:
        print("\nNull values: 0")

    # 2. Timestamp analysis
    try:
        # Parse timestamp safely
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="ISO8601", utc=True, errors='coerce')
        if df['Timestamp'].isnull().sum() > 0:
            print(f"Failed to parse {df['Timestamp'].isnull().sum()} timestamps.")
            df = df.dropna(subset=['Timestamp'])

        df = df.sort_values('Timestamp')
        
        is_monotonic = df['Timestamp'].is_monotonic_increasing
        print(f"\nMonotonic timestamps: {is_monotonic}")

        deltas = df['Timestamp'].diff().dt.total_seconds()
        print(f"\nTimestamp Delta Stats (seconds):")
        print(f"  Mean gap: {deltas.mean():.4f}")
        print(f"  Max gap:  {deltas.max():.4f}")
        print(f"  Min gap:  {deltas.min():.4f}")
        print(f"  Std dev:  {deltas.std():.4f}")

        # Significant gaps (e.g., > 1s)
        large_gaps = deltas[deltas > 1.0]
        if not large_gaps.empty:
            print(f"  WARNING: Found {len(large_gaps)} gaps larger than 1 second.")
    except Exception as e:
        print(f"\nError analyzing timestamps: {e}")

    # 3. Summary stats per axis
    print("\nSummary Statistics:")
    numeric_cols = ['Accel_X', 'Accel_Y', 'Accel_Z', 'Gyro_X', 'Gyro_Y', 'Gyro_Z']
    stats = df[numeric_cols].describe().loc[['mean', 'std', 'min', 'max']]
    print(stats)

if __name__ == '__main__':
    run_scan()
