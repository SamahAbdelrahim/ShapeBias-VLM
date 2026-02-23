"""View embeddings output in a simple, readable format."""

import json
from pathlib import Path

from config import TRIALS_INCLUDE

# Paths relative to project root
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
METADATA_PATH = OUTPUT_DIR / "metadata.json"


def main():
    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    if TRIALS_INCLUDE:
        filtered = [(i, m) for i, m in enumerate(metadata) if m["trial"] in TRIALS_INCLUDE]
        indices, metadata_sub = [x[0] for x in filtered], [x[1] for x in filtered]
        print(f"Filtered to trials: {TRIALS_INCLUDE} ({len(metadata_sub)} descriptions)\n")
    else:
        indices = list(range(len(metadata)))
        metadata_sub = metadata

    print("=" * 50)
    print(f"EMBEDDINGS INDEX ({len(metadata_sub)} descriptions)")
    print("=" * 50)
    print("\nEach row = one object description with its embedding\n")
    print(f"{'#':>4} | {'Trial':<20} | Object")
    print("-" * 50)

    for idx, row in zip(indices, metadata_sub):
        print(f"{idx:>4} | {row['trial']:<20} | {row['object_number']}")

    # Group by object_number (for cross-trial comparison)
    from collections import defaultdict
    by_object = defaultdict(list)
    for idx, row in zip(indices, metadata_sub):
        by_object[row["object_number"]].append((row["trial"], idx))

    print("\n" + "=" * 50)
    print("OBJECTS BY TRIAL (for comparing same object across trials)")
    print("=" * 50)
    for obj in sorted(by_object.keys(), key=lambda x: (len(x), x)):
        trials = by_object[obj]
        trial_str = ", ".join(f"{t} (#{i})" for t, i in trials)
        print(f"\n  Object {obj}: {trial_str}")

    # Export CSV for Excel
    csv_path = OUTPUT_DIR / "embeddings_index.csv"
    with open(csv_path, "w") as f:
        f.write("index,trial,object_number\n")
        for idx, row in zip(indices, metadata_sub):
            f.write(f"{idx},{row['trial']},{row['object_number']}\n")
    print(f"\n\nExported table to {csv_path} (open in Excel)")


if __name__ == "__main__":
    main()
