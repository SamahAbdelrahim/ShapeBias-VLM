"""
Level 2 analysis: Shared representational dimensions of objects as expressed in language.

Research question: What are the shared representational dimensions of objects
as expressed in language (from GPT embeddings)?

Uses:
  - PCA to find principal axes of variance (shared dimensions)
  - Across-trial stability: do dimensions replicate across trials?
  - Object loadings: which objects contribute to each dimension?
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from config import TRIALS_INCLUDE

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
DATA_DIR = PROJECT_ROOT / "data" / "gpt_txt_descriptions"
EMBEDDINGS_PATH = OUTPUT_DIR / "embeddings.npy"
METADATA_PATH = OUTPUT_DIR / "metadata.json"


def load_data():
    """Load embeddings, metadata, and optionally descriptions for interpretation."""
    embeddings = np.load(EMBEDDINGS_PATH)
    with open(METADATA_PATH) as f:
        metadata = json.load(f)
    return embeddings, metadata


def load_descriptions(metadata):
    """Reload descriptions from CSV in same order as metadata (trial, object_number)."""
    lookup = {}
    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        df = pd.read_csv(csv_path)
        desc_col = next((c for c in df.columns if "chatgpt response" in c.lower() and "description" in c.lower()), None)
        obj_col = next((c for c in df.columns if "object number" in c.lower()), None)
        if not desc_col or not obj_col:
            continue
        for _, row in df.iterrows():
            obj_num = str(row.get(obj_col, "")).strip()
            desc = str(row.get(desc_col, "")).strip()
            if obj_num and len(desc) >= 50:
                trial = csv_path.stem
                lookup[(trial, obj_num)] = desc

    return [lookup.get((m["trial"], m["object_number"]), "") for m in metadata]


def pca(X, n_components=10):
    """Center, run PCA. Uses thin SVD on X for efficiency (n < d)."""
    X_centered = X - X.mean(axis=0)
    # SVD of X: (n,d) -> U(n,n), S(min), Vt(min,d). PCs are rows of Vt.
    U, s, Vt = np.linalg.svd(X_centered, full_matrices=False)
    var_explained = (s ** 2) / (s ** 2).sum()
    n = min(n_components, len(s))
    loadings = U[:, :n] * s[:n]  # scores = U @ diag(s)
    components = Vt[:n].T  # (d, n) = PC directions
    return loadings, components, var_explained[:n], var_explained


def main():
    embeddings, metadata = load_data()

    # Filter to selected trials
    if TRIALS_INCLUDE:
        mask = [m["trial"] in TRIALS_INCLUDE for m in metadata]
        embeddings = embeddings[mask]
        metadata = [m for m, ok in zip(metadata, mask) if ok]
        print(f"Filtered to trials: {TRIALS_INCLUDE}")

    n_samples, n_dims = embeddings.shape

    print("=" * 70)
    print("LEVEL 2: Shared Representational Dimensions")
    print("=" * 70)
    print(f"\nData: {n_samples} descriptions, {n_dims} embedding dimensions (GPT text-embedding-3-large)")

    # Center embeddings (standard for PCA)
    X = embeddings - embeddings.mean(axis=0)

    # --- PCA on embeddings ---
    print("\n" + "-" * 70)
    print("1. PRINCIPAL COMPONENTS (shared dimensions across all descriptions)")
    print("-" * 70)

    n_components = 15
    loadings, components, var_top, var_all = pca(embeddings, n_components)

    print("\nVariance explained per component:")
    cumvar = 0
    for i in range(n_components):
        cumvar += var_all[i]
        print(f"  PC{i+1:2d}: {var_all[i]*100:5.2f}%  (cumulative: {cumvar*100:5.1f}%)")

    # Which descriptions load highest/lowest on each PC (for interpretation)
    print("\n" + "-" * 70)
    print("2. TOP & BOTTOM LOADINGS (interpret what each dimension captures)")
    print("-" * 70)

    descriptions = None
    if DATA_DIR.exists():
        try:
            descriptions = load_descriptions(metadata)
        except Exception:
            pass

    for pc in range(min(5, n_components)):
        idx = np.argsort(loadings[:, pc])
        hi_idx, lo_idx = list(idx[-3:][::-1]), list(idx[:3])
        print(f"\nPC{pc+1} (explains {var_all[pc]*100:.1f}% variance):")
        def label(m):
            t = m["trial"].replace("trial", "t").replace("_winter_26", "")
            return f"{m['object_number']}({t})"
        print("  High (+):", ", ".join(label(metadata[i]) for i in hi_idx))
        print("  Low (-): ", ", ".join(label(metadata[i]) for i in lo_idx))
        if descriptions:
            print("  Sample high:", (descriptions[hi_idx[0]][:80] + "..." if len(descriptions[hi_idx[0]]) > 80 else descriptions[hi_idx[0]]))

    # --- Object-level aggregation ---
    print("\n" + "-" * 70)
    print("3. OBJECT LOADINGS (avg per object, across trials)")
    print("-" * 70)

    by_object = defaultdict(list)
    for i, m in enumerate(metadata):
        by_object[m["object_number"]].append((loadings[i], m["trial"]))

    obj_loadings = {}
    for obj, entries in by_object.items():
        arr = np.array([e[0] for e in entries])
        obj_loadings[obj] = arr.mean(axis=0)

    obj_keys = sorted(obj_loadings.keys(), key=lambda x: (len(x), x))
    obj_matrix = np.array([obj_loadings[o] for o in obj_keys])

    print("\nObjects most associated with each PC (object-level):")
    for pc in range(min(5, n_components)):
        vals = obj_matrix[:, pc]
        order = np.argsort(vals)
        top = [obj_keys[i] for i in order[-5:][::-1]]
        bottom = [obj_keys[i] for i in order[:5]]
        print(f"  PC{pc+1}: high={top}, low={bottom}")

    # --- Across-trial stability of dimensions ---
    print("\n" + "-" * 70)
    print("4. ACROSS-TRIAL STABILITY (do dimensions replicate?)")
    print("-" * 70)

    by_trial = defaultdict(list)
    for i, m in enumerate(metadata):
        by_trial[m["trial"]].append((i, m["object_number"]))

    trials = sorted(by_trial.keys())
    if len(trials) >= 2:
        # Use objects that appear in ALL trials
        all_objs = set(m[1] for m in by_trial[trials[0]])
        for t in trials[1:]:
            all_objs &= set(m[1] for m in by_trial[t])
        common_objs = sorted(all_objs, key=lambda x: (len(x), x))

        if len(common_objs) >= 3:
            print(f"\nUsing {len(common_objs)} objects common to all trials: {common_objs[:8]}{'...' if len(common_objs)>8 else ''}")
            trial_embeddings = {}
            for t in trials:
                idx = [i for o in common_objs for i, obj in by_trial[t] if obj == o]
                trial_embeddings[t] = embeddings[idx]

            # Correlate PC1 directions across trials
            pcs = {}
            for t in trials:
                _, comps, _, _ = pca(trial_embeddings[t], 5)
                pcs[t] = comps[:, 0]  # first PC direction

            pc1_correlations = {}
            print("\nCorrelation of PC1 direction across trials:")
            for i, t1 in enumerate(trials):
                for t2 in trials[i+1:]:
                    c = np.corrcoef(pcs[t1], pcs[t2])[0, 1]
                    pc1_correlations[f"{t1}_vs_{t2}"] = float(c)
                    print(f"  {t1:<20} vs {t2:<20}: r = {c:.3f}")
        else:
            pc1_correlations = {}
            print("\n(Need 3+ common objects across trials for stability analysis)")
    else:
        pc1_correlations = {}
        print("\n(Need 2+ trials for stability analysis)")

    # --- Save outputs ---
    out = {
        "variance_explained": {f"PC{i+1}": float(var_all[i]) for i in range(n_components)},
        "object_loadings": {obj: [float(x) for x in obj_loadings[obj]] for obj in obj_keys},
        "n_components": n_components,
        "trials_include": TRIALS_INCLUDE,
        "pc1_correlations_across_trials": pc1_correlations,
    }
    with open(OUTPUT_DIR / "level2_shared_dimensions.json", "w") as f:
        json.dump(out, f, indent=2)

    np.save(OUTPUT_DIR / "level2_loadings.npy", loadings)
    np.save(OUTPUT_DIR / "level2_components.npy", components)
    with open(OUTPUT_DIR / "level2_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 70)
    print("Saved: level2_shared_dimensions.json, level2_loadings.npy, level2_components.npy, level2_metadata.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
