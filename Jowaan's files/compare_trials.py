"""
Compare Trials (1/2/3) - ChatGPT Object Descriptions
Embedding-based similarity analysis

Outputs for each pair:
  - comparison_<A>_vs_<B>.png
  - comparison_<A>_vs_<B>_results.json
  - comparison_<A>_vs_<B>_report.txt
"""

import os
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = "data"

TRIAL_FILES = {
    1: "Trial_1.xlsx",
    2: "Trial_2.xlsx",
    3: "Trial_3.xlsx",
}

DESC_COL = "chatgpt response - description"
MIN_DESC_LEN = 10

TSNE_RANDOM_STATE = 42
TSNE_MAX_PERPLEXITY = 30

# -----------------------------
# HELPERS
# -----------------------------
def ensure_cwd_to_script_dir():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


def load_trial(trial_num: int) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, TRIAL_FILES[trial_num])
    df = pd.read_excel(path)
    print(f"  ✓ Trial {trial_num}: Loaded {len(df)} rows from {path}")
    return df


def add_object_id(df: pd.DataFrame, trial_num: int) -> pd.DataFrame:
    # Uses the first two columns as (object_num, object_letter), same as your original script.
    obj_num_col = df.columns[0]
    obj_letter_col = df.columns[1]
    df = df.copy()
    df["object_id"] = df[obj_num_col].astype(str) + "_" + df[obj_letter_col].astype(str)
    return df


def filter_valid_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df[DESC_COL].notna()].copy()
    df = df[df[DESC_COL].astype(str).str.len() > MIN_DESC_LEN].copy()
    return df


def encode_descriptions(model: SentenceTransformer, df: pd.DataFrame) -> np.ndarray:
    descriptions = df[DESC_COL].astype(str).tolist()
    return model.encode(descriptions, show_progress_bar=True)


def safe_perplexity(n_points: int, max_perplexity: int = TSNE_MAX_PERPLEXITY) -> int:
    # TSNE requires perplexity < n_samples
    return max(2, min(max_perplexity, n_points - 1))


def compare_trials(trial_a: int, trial_b: int,
                   df_a: pd.DataFrame, emb_a: np.ndarray,
                   df_b: pd.DataFrame, emb_b: np.ndarray):
    print("\n" + "=" * 80)
    print(f"COMPARING TRIAL {trial_a} vs TRIAL {trial_b}")
    print("=" * 80)

    # Average similarity across all pairs
    sim_matrix = cosine_similarity(emb_a, emb_b)
    avg_similarity = float(np.mean(sim_matrix))

    print(f"\nAverage similarity: {avg_similarity:.3f}")
    if avg_similarity > 0.85:
        print("  → VERY SIMILAR descriptions! 🟢")
    elif avg_similarity > 0.70:
        print("  → Moderately similar 🟡")
    else:
        print("  → Different descriptions 🟠")

    # Object-by-object similarity for common objects
    objects_a = set(df_a["object_id"].unique())
    objects_b = set(df_b["object_id"].unique())
    common_objects = sorted(objects_a.intersection(objects_b))
    print(f"\nCommon objects: {len(common_objects)}")

    object_similarities = []
    object_similarities_sorted = []

    if common_objects:
        print("\nPer-object similarities:")
        for obj_id in common_objects:
            idx_a = df_a[df_a["object_id"] == obj_id].index[0]
            emb_a_idx = df_a.index.get_loc(idx_a)
            vec_a = emb_a[emb_a_idx]

            idx_b = df_b[df_b["object_id"] == obj_id].index[0]
            emb_b_idx = df_b.index.get_loc(idx_b)
            vec_b = emb_b[emb_b_idx]

            sim = float(cosine_similarity([vec_a], [vec_b])[0][0])
            object_similarities.append({"object_id": obj_id, "similarity": sim})
            print(f"  {obj_id}: {sim:.3f}")

        object_similarities_sorted = sorted(object_similarities, key=lambda x: x["similarity"], reverse=True)

        print(f"\nMost similar: {object_similarities_sorted[0]['object_id']} "
              f"({object_similarities_sorted[0]['similarity']:.3f})")
        print(f"Least similar: {object_similarities_sorted[-1]['object_id']} "
              f"({object_similarities_sorted[-1]['similarity']:.3f})")

    # t-SNE visualization
    print("\nCreating t-SNE visualization...")
    all_embeddings = np.vstack([emb_a, emb_b])
    labels = [f"Trial {trial_a}"] * len(emb_a) + [f"Trial {trial_b}"] * len(emb_b)

    perplexity = safe_perplexity(len(all_embeddings))
    tsne = TSNE(n_components=2, random_state=TSNE_RANDOM_STATE, perplexity=perplexity)
    emb2d = tsne.fit_transform(all_embeddings)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Use default matplotlib colors (no seaborn, no hardcoded palette needed)
    mask_a = np.array(labels) == f"Trial {trial_a}"
    mask_b = np.array(labels) == f"Trial {trial_b}"

    ax.scatter(emb2d[mask_a, 0], emb2d[mask_a, 1], label=f"Trial {trial_a}", alpha=0.7, s=100)
    ax.scatter(emb2d[mask_b, 0], emb2d[mask_b, 1], label=f"Trial {trial_b}", alpha=0.7, s=100)

    ax.set_xlabel("t-SNE Dimension 1", fontsize=12)
    ax.set_ylabel("t-SNE Dimension 2", fontsize=12)
    ax.set_title(
        f"Trial {trial_a} vs Trial {trial_b} Semantic Comparison\n(Closer points = More similar descriptions)",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    png_path = f"comparison_trial{trial_a}_vs_trial{trial_b}.png"
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  ✓ Saved: {png_path}")

    # Save results JSON
    results = {
        "trial_a": trial_a,
        "trial_b": trial_b,
        "average_similarity": avg_similarity,
        "trial_a_count": int(len(df_a)),
        "trial_b_count": int(len(df_b)),
        "common_objects": int(len(common_objects)),
        "object_similarities": object_similarities,
    }

    json_path = f"comparison_trial{trial_a}_vs_trial{trial_b}_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  ✓ Saved: {json_path}")

    # Save text report
    report_path = f"comparison_trial{trial_a}_vs_trial{trial_b}_report.txt"
    with open(report_path, "w") as f:
        f.write(f"TRIAL {trial_a} vs TRIAL {trial_b} COMPARISON REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Average similarity: {avg_similarity:.3f}\n")
        f.write(f"Trial {trial_a} descriptions: {len(df_a)}\n")
        f.write(f"Trial {trial_b} descriptions: {len(df_b)}\n")
        f.write(f"Common objects: {len(common_objects)}\n\n")

        if avg_similarity > 0.85:
            interpretation = "VERY SIMILAR - Trial settings likely had minimal effect"
        elif avg_similarity > 0.70:
            interpretation = "MODERATELY SIMILAR - Some differences between trials"
        else:
            interpretation = "DIFFERENT - Trial settings significantly affected descriptions"

        f.write(f"Interpretation: {interpretation}\n\n")

        if common_objects:
            f.write("Per-object similarities:\n")
            f.write("-" * 70 + "\n")
            for obj in object_similarities_sorted:
                f.write(f"  {obj['object_id']:10s}: {obj['similarity']:.3f}\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Most similar object: {object_similarities_sorted[0]['object_id']} "
                    f"(similarity: {object_similarities_sorted[0]['similarity']:.3f})\n")
            f.write(f"Least similar object: {object_similarities_sorted[-1]['object_id']} "
                    f"(similarity: {object_similarities_sorted[-1]['similarity']:.3f})\n")

    print(f"  ✓ Saved: {report_path}")

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"Key finding: Similarity = {avg_similarity:.3f}")
    print("Generated files:")
    print(f"  1. {png_path}")
    print(f"  2. {report_path}")
    print(f"  3. {json_path}")
    print("=" * 80)


def main():
    ensure_cwd_to_script_dir()

    print("=" * 80)
    print("COMPARING TRIALS (1, 2, 3)")
    print("=" * 80)

    # Load trials
    print("\nLoading trials...")
    df1 = load_trial(1)
    df2 = load_trial(2)
    df3 = load_trial(3)

    print("\nColumn names found:")
    print(f"  Trial 1: {df1.columns.tolist()}")
    print(f"  Trial 2: {df2.columns.tolist()}")
    print(f"  Trial 3: {df3.columns.tolist()}")

    # Add object ids + filter valid descriptions
    df1 = filter_valid_descriptions(add_object_id(df1, 1))
    df2 = filter_valid_descriptions(add_object_id(df2, 2))
    df3 = filter_valid_descriptions(add_object_id(df3, 3))

    print("\nValid descriptions:")
    print(f"  Trial 1: {len(df1)}")
    print(f"  Trial 2: {len(df2)}")
    print(f"  Trial 3: {len(df3)}")

    # Load embedding model once
    print("\nLoading embedding model (first time will download ~80MB)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Embed each trial once
    print("\nGenerating embeddings for Trial 1...")
    emb1 = encode_descriptions(model, df1)

    print("\nGenerating embeddings for Trial 2...")
    emb2 = encode_descriptions(model, df2)

    print("\nGenerating embeddings for Trial 3...")
    emb3 = encode_descriptions(model, df3)

    # Pairwise comparisons
    compare_trials(1, 2, df1, emb1, df2, emb2)
    compare_trials(2, 3, df2, emb2, df3, emb3)
    compare_trials(1, 3, df1, emb1, df3, emb3)


if __name__ == "__main__":
    main()