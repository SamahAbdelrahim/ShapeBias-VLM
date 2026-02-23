"""Compute cosine similarity between descriptions of the same object across trials."""

import json
from pathlib import Path

import numpy as np

from config import TRIALS_INCLUDE


def cosine_similarity(vecs):
    """Compute pairwise cosine similarity between rows. Returns NxN matrix."""
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    normalized = vecs / norms
    return np.dot(normalized, normalized.T)

# Paths
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
EMBEDDINGS_PATH = OUTPUT_DIR / "embeddings.npy"
METADATA_PATH = OUTPUT_DIR / "metadata.json"


def main():
    embeddings = np.load(EMBEDDINGS_PATH)
    with open(METADATA_PATH) as f:
        metadata = json.load(f)

    # Filter to selected trials
    if TRIALS_INCLUDE:
        mask = [m["trial"] in TRIALS_INCLUDE for m in metadata]
        embeddings = embeddings[mask]
        metadata = [m for m, ok in zip(metadata, mask) if ok]
        print(f"Filtered to trials: {TRIALS_INCLUDE}\n")

    # Group by object_number: {object: [(trial, index), ...]}
    from collections import defaultdict
    by_object = defaultdict(list)
    for i, row in enumerate(metadata):
        by_object[row["object_number"]].append((row["trial"], i))

    print("=" * 70)
    print("COSINE SIMILARITY (same object, different trials)")
    print("=" * 70)
    print("1.0 = identical descriptions, lower = less similar\n")

    results = []
    for obj in sorted(by_object.keys(), key=lambda x: (len(x), x)):
        entries = by_object[obj]
        if len(entries) < 2:
            continue  # Skip objects with only one trial

        trials = [e[0] for e in entries]
        indices = [e[1] for e in entries]
        vecs = embeddings[indices]

        sim_matrix = cosine_similarity(vecs)

        print(f"Object {obj}")
        for i in range(len(trials)):
            for j in range(i + 1, len(trials)):
                sim = sim_matrix[i, j]
                print(f"  {trials[i]:<20} vs {trials[j]:<20} : {sim:.4f}")
                results.append({
                    "object_number": obj,
                    "trial_a": trials[i],
                    "trial_b": trials[j],
                    "cosine_similarity": round(float(sim), 4),
                })
        print()

    # Export to JSON
    out_path = OUTPUT_DIR / "cosine_similarity_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # Export to CSV
    csv_path = OUTPUT_DIR / "cosine_similarity_results.csv"
    with open(csv_path, "w") as f:
        f.write("object_number,trial_a,trial_b,cosine_similarity\n")
        for r in results:
            f.write(f"{r['object_number']},{r['trial_a']},{r['trial_b']},{r['cosine_similarity']}\n")

    print(f"Saved: {out_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
