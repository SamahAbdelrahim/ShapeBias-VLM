"""
Compare Trial 3 vs Trial 1 - ChatGPT Object Descriptions
Embedding-based similarity analysis
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

# Make sure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("COMPARING TRIAL 3 vs TRIAL 1")
print("=" * 80)

# Load Trial 3
print("\nLoading Trial 3...")
df_trial3 = pd.read_excel('data/Trial_3.xlsx')
print(f"  ✓ Loaded {len(df_trial3)} rows")

# Load Trial 1
print("Loading Trial 1...")
df_trial1 = pd.read_excel('data/Trial_1.xlsx')
print(f"  ✓ Loaded {len(df_trial1)} rows")

# Show column names
print(f"\nColumn names found:")
print(f"  Trial 3: {df_trial3.columns.tolist()}")
print(f"  Trial 1: {df_trial1.columns.tolist()}")

# Create object IDs
trial3_obj_num_col = df_trial3.columns[0]
trial3_obj_letter_col = df_trial3.columns[1]
df_trial3['object_id'] = (df_trial3[trial3_obj_num_col].astype(str) + '_' +
                          df_trial3[trial3_obj_letter_col].astype(str))

trial1_obj_num_col = df_trial1.columns[0]
trial1_obj_letter_col = df_trial1.columns[1]
df_trial1['object_id'] = (df_trial1[trial1_obj_num_col].astype(str) + '_' +
                          df_trial1[trial1_obj_letter_col].astype(str))

# Filter valid descriptions
df_trial3 = df_trial3[df_trial3['chatgpt response - description'].notna()].copy()
df_trial3 = df_trial3[df_trial3['chatgpt response - description'].astype(str).str.len() > 10].copy()

df_trial1 = df_trial1[df_trial1['chatgpt response - description'].notna()].copy()
df_trial1 = df_trial1[df_trial1['chatgpt response - description'].astype(str).str.len() > 10].copy()

print(f"\nValid descriptions:")
print(f"  Trial 3: {len(df_trial3)}")
print(f"  Trial 1: {len(df_trial1)}")

# Load embedding model
print("\nLoading embedding model (first time will download ~80MB)...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Generate embeddings
print("\nGenerating embeddings for Trial 3...")
descriptions_trial3 = df_trial3['chatgpt response - description'].tolist()
embeddings_trial3 = model.encode(descriptions_trial3, show_progress_bar=True)

print("\nGenerating embeddings for Trial 1...")
descriptions_trial1 = df_trial1['chatgpt response - description'].tolist()
embeddings_trial1 = model.encode(descriptions_trial1, show_progress_bar=True)

# Calculate similarity
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

similarity_matrix = cosine_similarity(embeddings_trial3, embeddings_trial1)
avg_similarity = np.mean(similarity_matrix)

print(f"\nAverage similarity: {avg_similarity:.3f}")
if avg_similarity > 0.85:
    print("  → VERY SIMILAR descriptions! 🟢")
elif avg_similarity > 0.70:
    print("  → Moderately similar 🟡")
else:
    print("  → Different descriptions 🟠")

# Object-by-object comparison
objects_trial3 = set(df_trial3['object_id'].unique())
objects_trial1 = set(df_trial1['object_id'].unique())
common_objects = objects_trial3.intersection(objects_trial1)

print(f"\nCommon objects: {len(common_objects)}")

if len(common_objects) > 0:
    print(f"\nPer-object similarities:")
    object_similarities = []

    for obj_id in sorted(common_objects):
        idx3 = df_trial3[df_trial3['object_id'] == obj_id].index[0]
        emb3_idx = df_trial3.index.get_loc(idx3)
        emb3 = embeddings_trial3[emb3_idx]

        idx1 = df_trial1[df_trial1['object_id'] == obj_id].index[0]
        emb1_idx = df_trial1.index.get_loc(idx1)
        emb1 = embeddings_trial1[emb1_idx]

        sim = cosine_similarity([emb3], [emb1])[0][0]
        object_similarities.append({'object_id': obj_id, 'similarity': float(sim)})
        print(f"  {obj_id}: {sim:.3f}")

    object_similarities_sorted = sorted(object_similarities,
                                        key=lambda x: x['similarity'],
                                        reverse=True)

    print(f"\nMost similar: {object_similarities_sorted[0]['object_id']} "
          f"({object_similarities_sorted[0]['similarity']:.3f})")
    print(f"Least similar: {object_similarities_sorted[-1]['object_id']} "
          f"({object_similarities_sorted[-1]['similarity']:.3f})")

# Create t-SNE visualization
print("\nCreating t-SNE visualization...")
all_embeddings = np.vstack([embeddings_trial3, embeddings_trial1])
labels = ['Trial 3'] * len(embeddings_trial3) + ['Trial 1'] * len(embeddings_trial1)

tsne = TSNE(n_components=2, random_state=42,
            perplexity=min(30, len(all_embeddings) - 1))
embeddings_2d = tsne.fit_transform(all_embeddings)

fig, ax = plt.subplots(figsize=(12, 8))

colors = {'Trial 3': '#FF6B6B', 'Trial 1': '#4ECDC4'}
for trial_name in ['Trial 3', 'Trial 1']:
    mask = np.array(labels) == trial_name
    ax.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1],
               label=trial_name, alpha=0.7, s=100, color=colors[trial_name])

ax.set_xlabel('t-SNE Dimension 1', fontsize=12)
ax.set_ylabel('t-SNE Dimension 2', fontsize=12)
ax.set_title('Trial 3 vs Trial 1 Semantic Comparison\n(Closer points = More similar descriptions)',
             fontsize=14, fontweight='bold')
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comparison_trial3_vs_trial1.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: comparison_trial3_vs_trial1.png")
plt.close()

# Save results
results = {
    'average_similarity': float(avg_similarity),
    'trial3_count': len(df_trial3),
    'trial1_count': len(df_trial1),
    'common_objects': len(common_objects),
    'object_similarities': object_similarities if len(common_objects) > 0 else []
}

with open('comparison_results.json', 'w') as f:
    json.dump(results, f, indent=2)

with open('comparison_report.txt', 'w') as f:
    f.write("TRIAL 3 vs TRIAL 1 COMPARISON REPORT\n")
    f.write("=" * 70 + "\n\n")
    f.write(f"Average similarity: {avg_similarity:.3f}\n")
    f.write(f"Trial 3 descriptions: {len(df_trial3)}\n")
    f.write(f"Trial 1 descriptions: {len(df_trial1)}\n")
    f.write(f"Common objects: {len(common_objects)}\n\n")

    if avg_similarity > 0.85:
        interpretation = "VERY SIMILAR - Trial settings likely had minimal effect"
    elif avg_similarity > 0.70:
        interpretation = "MODERATELY SIMILAR - Some differences between trials"
    else:
        interpretation = "DIFFERENT - Trial settings significantly affected descriptions"

    f.write(f"Interpretation: {interpretation}\n\n")

    if len(common_objects) > 0:
        f.write("Per-object similarities:\n")
        f.write("-" * 70 + "\n")
        for obj in object_similarities_sorted:
            f.write(f"  {obj['object_id']:10s}: {obj['similarity']:.3f}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write(f"Most similar object: {object_similarities_sorted[0]['object_id']} ")
        f.write(f"(similarity: {object_similarities_sorted[0]['similarity']:.3f})\n")
        f.write(f"Least similar object: {object_similarities_sorted[-1]['object_id']} ")
        f.write(f"(similarity: {object_similarities_sorted[-1]['similarity']:.3f})\n")

print("  ✓ Saved: comparison_results.json")
print("  ✓ Saved: comparison_report.txt")

print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE!")
print("=" * 80)
print(f"\nKey finding: Similarity = {avg_similarity:.3f}")
print("\nGenerated files:")
print("  1. comparison_trial3_vs_trial1.png - Visual comparison")
print("  2. comparison_report.txt - Detailed text report")
print("  3. comparison_results.json - Data for further analysis")
print("\n" + "=" * 80)