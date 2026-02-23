"""
Interpret PCA dimensions and create visualizations.

How to interpret:
  1. For each PC, read the HIGH vs LOW loading descriptions
  2. Ask: What do high loaders have in common? What do low loaders have?
  3. The contrast defines the dimension → propose a name (e.g., "rigidity", "colorfulness")
"""

import json
import os
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
LOADINGS_PATH = OUTPUT_DIR / "level2_loadings.npy"


def load_descriptions(metadata):
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


def main():
    if not LOADINGS_PATH.exists():
        print("Run level2_shared_dimensions.py first to generate PCA outputs.")
        return

    # Use filtered metadata (matches loadings) when available
    metadata_path = OUTPUT_DIR / "level2_metadata.json"
    if metadata_path.exists():
        metadata = json.load(open(metadata_path))
    else:
        metadata = json.load(open(METADATA_PATH))
    loadings = np.load(LOADINGS_PATH)
    with open(OUTPUT_DIR / "level2_shared_dimensions.json") as f:
        data = json.load(f)
    var = data["variance_explained"]
    obj_loadings = data["object_loadings"]
    obj_keys = sorted(obj_loadings.keys(), key=lambda x: (len(x), x))

    descriptions = []
    if DATA_DIR.exists():
        try:
            descriptions = load_descriptions(metadata)
        except Exception:
            pass

    n_components = min(5, loadings.shape[1])
    n_extreme = 4  # top/bottom N per PC

    # --- 1. Interpretation report (markdown) ---
    report = []
    report.append("# PC Dimension Interpretation Guide\n")
    if TRIALS_INCLUDE:
        report.append(f"**Trials included:** {', '.join(TRIALS_INCLUDE)}\n")
    report.append("**How to interpret:** For each PC, read the HIGH vs LOW descriptions.")
    report.append("What do high loaders share? What do low loaders share? The contrast = the dimension.\n")

    for pc in range(n_components):
        idx = np.argsort(loadings[:, pc])
        hi_idx = list(idx[-n_extreme:][::-1])
        lo_idx = list(idx[:n_extreme])

        report.append(f"\n---\n## PC{pc+1} ({var.get(f'PC{pc+1}', 0)*100:.1f}% variance)\n")

        report.append("\n### HIGH loaders (+) – what do these share?\n")
        for i in hi_idx:
            m = metadata[i]
            report.append(f"- **{m['object_number']}** ({m['trial']})\n")
            if descriptions and descriptions[i]:
                text = descriptions[i].replace("\n", " ")[:400]
                report.append(f"  > {text}...\n")
            report.append("")

        report.append("\n### LOW loaders (-) – what do these share?\n")
        for i in lo_idx:
            m = metadata[i]
            report.append(f"- **{m['object_number']}** ({m['trial']})\n")
            if descriptions and descriptions[i]:
                text = descriptions[i].replace("\n", " ")[:400]
                report.append(f"  > {text}...\n")
            report.append("")

        report.append("\n**Your proposed name for this dimension:** _______________\n")

    report_path = OUTPUT_DIR / "pc_interpretation_guide.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report))
    print(f"Saved interpretation guide: {report_path}")

    # --- 2. Visualizations ---
    try:
        os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT_DIR / "mpl_cache"))
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        print("Install matplotlib for visualizations: pip install matplotlib")
        return

    # 2a. PC1 vs PC2 scatter (descriptions)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    trials = list({m["trial"] for m in metadata})
    colors = plt.cm.tab10(np.linspace(0, 1, len(trials)))
    trial_to_color = dict(zip(trials, colors))

    ax = axes[0]
    for i, m in enumerate(metadata):
        c = trial_to_color.get(m["trial"], "gray")
        ax.scatter(loadings[i, 0], loadings[i, 1], c=[c], s=30, alpha=0.7)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    title = "Descriptions in PC1–PC2 space (colored by trial)"
    if TRIALS_INCLUDE:
        title += f"\nTrials: {TRIALS_INCLUDE}"
    pc1_corr = data.get("pc1_correlations_across_trials", {})
    if pc1_corr:
        vals = list(pc1_corr.values())
        corr_str = f"r = {vals[0]:.3f}" if len(vals) == 1 else ", ".join(f"r={v:.3f}" for v in vals)
        title += f"\nPC1 stability (across trials): {corr_str}"
    ax.set_title(title, fontsize=9)
    ax.axhline(0, color="k", alpha=0.2, linestyle="--")
    ax.axvline(0, color="k", alpha=0.2, linestyle="--")
    ax.legend(
        [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, label=t) for t, c in trial_to_color.items()],
        [t for t in trials],
        fontsize=8,
    )

    # 2b. Object loadings bar chart (top 5 PCs, object-level)
    ax = axes[1]
    obj_matrix = np.array([[obj_loadings[o][pc] for pc in range(n_components)] for o in obj_keys])
    x = np.arange(len(obj_keys))
    width = 0.15
    for pc in range(n_components):
        offset = (pc - n_components / 2) * width
        ax.bar(x + offset, obj_matrix[:, pc], width, label=f"PC{pc+1} ({var.get(f'PC{pc+1}',0)*100:.0f}%)")
    ax.set_xticks(x)
    ax.set_xticklabels(obj_keys, rotation=45, ha="right")
    ax.set_xlabel("Object")
    ax.set_ylabel("Loading")
    ax.set_title("Object loadings per PC")
    ax.legend(fontsize=7)
    ax.axhline(0, color="k", alpha=0.3)

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "pc1_pc2_scatter_and_loadings.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: pc1_pc2_scatter_and_loadings.png")

    # 2c. Per-PC object loadings (horizontal bar)
    fig2, axes2 = plt.subplots(2, 3, figsize=(12, 8))
    axes2 = axes2.flatten()

    for pc in range(n_components):
        ax = axes2[pc]
        vals = obj_matrix[:, pc]
        order = np.argsort(vals)
        objs = [obj_keys[i] for i in order]
        v = [vals[i] for i in order]
        colors_bar = ["#2ecc71" if x > 0 else "#e74c3c" for x in v]
        ax.barh(objs, v, color=colors_bar, alpha=0.8)
        ax.axvline(0, color="k", alpha=0.3)
        ax.set_xlabel("Loading")
        ax.set_title(f"PC{pc+1} ({var.get(f'PC{pc+1}',0)*100:.1f}%)")
        ax.invert_yaxis()

    axes2[-1].axis("off")
    plt.suptitle("Object loadings per dimension (green=positive, red=negative)", y=1.02)
    plt.tight_layout()
    fig2.savefig(OUTPUT_DIR / "pc_object_loadings_per_dimension.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: pc_object_loadings_per_dimension.png")

    # 2d. Across-trial stability (PC1 correlation)
    pc1_corr = data.get("pc1_correlations_across_trials", {})
    if pc1_corr:
        fig_stab, ax_stab = plt.subplots(figsize=(5, 3))
        pairs = list(pc1_corr.keys())
        vals = [pc1_corr[k] for k in pairs]
        labels = [k.replace("_winter_26", "").replace("_vs_", " vs ") for k in pairs]
        ax_stab.barh(labels, vals, color="steelblue", alpha=0.8)
        ax_stab.axvline(0, color="k", alpha=0.3)
        ax_stab.set_xlim(-1, 1)
        ax_stab.set_xlabel("Correlation of PC1 direction")
        ax_stab.set_title("Across-trial stability\n(Higher = same latent dimension in both trials)")
        fig_stab.tight_layout()
        fig_stab.savefig(OUTPUT_DIR / "pc1_stability_across_trials.png", dpi=150, bbox_inches="tight")
        plt.close(fig_stab)
        print(f"Saved: pc1_stability_across_trials.png")

    # 2e. Scree plot
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    var_list = [var.get(f"PC{i+1}", 0) * 100 for i in range(15)]
    ax3.bar(range(1, 16), var_list, color="steelblue", alpha=0.8)
    ax3.set_xlabel("Principal component")
    ax3.set_ylabel("Variance explained (%)")
    ax3.set_title("Scree plot: variance explained per PC\n(15% = how much of total variance PC1 captures)")
    fig3.savefig(OUTPUT_DIR / "scree_plot.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: scree_plot.png")

    print("\nTo interpret: open pc_interpretation_guide.md and read HIGH vs LOW descriptions for each PC.")


if __name__ == "__main__":
    main()
