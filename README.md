# Embedding-Based Probing for Object Descriptions

This toolkit analyzes semantic structure in object descriptions using embedding-based probing techniques. It's designed to compare how ChatGPT and humans describe objects, and to identify the dominant semantic dimensions in these descriptions.

## Overview

The analysis pipeline:

1. **Embeds descriptions** using sentence transformers
2. **Performs PCA** within each object to find semantic dimensions
3. **Identifies patterns** like geometry vs. surface, material vs. color, shape vs. detail
4. **Compares across trials** (Trial 1, 2, 3) and between ChatGPT and human data
5. **Visualizes results** with t-SNE plots, variance explained charts, and heatmaps

## Installation

```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Or install individually
pip install sentence-transformers pandas numpy scikit-learn matplotlib seaborn openpyxl --break-system-packages
```

## Quick Start

### 1. Basic Analysis (Single Trial)

```python
from embedding_probing_analysis import EmbeddingProber

# Initialize
prober = EmbeddingProber(model_name='all-MiniLM-L6-v2')

# Load your data
df = prober.load_data('chatgpt_generated_responses_and_images.xlsx')

# Generate embeddings
prober.generate_embeddings(df)

# Perform PCA analysis
prober.perform_pca_analysis(n_components=5)

# Analyze semantic dimensions
results = prober.analyze_semantic_dimensions(df)

# Save results
prober.save_results(results, 'semantic_analysis_results.json')

# Create visualizations
prober.visualize_results('output_figures')
```

### 2. Multi-Trial Comparison

```python
from trial_comparison import TrialComparator

# Initialize
comparator = TrialComparator()

# Load multiple trials
comparator.load_trial_data('Trial_1', 'trial1.xlsx')
comparator.load_trial_data('Trial_2', 'trial2.xlsx')
comparator.load_trial_data('Trial_3', 'trial3.xlsx')
comparator.load_trial_data('Human_Data', 'human_descriptions.xlsx')

# Generate comparison visualizations
comparator.visualize_trial_comparison('comparison_figures')

# Generate text report
comparator.generate_comparison_report('comparison_report.txt')
```

## Data Format

Your Excel file should have these columns:
- `object number`: Object identifier (e.g., "1A", "2B")
- `object letter`: Additional object identifier
- `chatgpt response - description`: The text descriptions to analyze
- (Optional) `video link`: Link to object video
- (Optional) Other metadata columns

The scripts will automatically:
- Combine `object number` + `object letter` into a unique object ID
- Filter out rows with missing descriptions
- Handle multiple descriptions per object

## Output Files

### 1. `semantic_analysis_results.json`
Contains detailed PCA results for each object:
```json
{
  "1A_A": {
    "object_id": "1A_A",
    "n_descriptions": 5,
    "explained_variance": [0.65, 0.20, 0.10, 0.03, 0.02],
    "components": {
      "PC1": {
        "variance_explained": 0.65,
        "high_loading_descriptions": ["..."],
        "low_loading_descriptions": ["..."]
      }
    }
  }
}
```

### 2. Visualizations

**Variance Explained Plots:**
- Shows how much variance each PC explains
- Helps identify how many meaningful dimensions exist

**PCA Scatter Plots:**
- One plot per object showing description clustering
- Points close together = similar descriptions
- Points far apart = different semantic emphasis

**t-SNE Comparison (multi-trial):**
- Shows all trials in 2D space
- Clusters indicate similar description patterns

**Similarity Heatmap (multi-trial):**
- Shows cosine similarity between trials
- Higher values = more similar descriptions

## Interpreting Results

### Principal Component Analysis

**PC1 (First Principal Component):**
- Captures the **primary axis of variation** in descriptions
- Often represents fundamental trade-offs like:
  - Global shape vs. local details
  - Material properties vs. geometric features
  - Color/texture vs. structure

**High variance explained by PC1:**
- Indicates descriptions vary along one main dimension
- Example: Some describe shape, others describe material

**Low variance explained by PC1:**
- Descriptions are more multidimensional
- Variation is spread across multiple semantic axes

### Semantic Dimensions

Look at high vs. low loading descriptions for each PC:

**Example Pattern 1: Geometry vs. Surface**
- **High loading:** "white crinkled paper," "textured exterior," "rough surface"
- **Low loading:** "cylindrical shape," "rounded form," "compact structure"
- **Interpretation:** PC1 separates surface descriptions from shape descriptions

**Example Pattern 2: Material vs. Color**
- **High loading:** "made of paper," "solid interior," "layered construction"
- **Low loading:** "bright white," "dark gray inside," "contrast between colors"

### Comparison Metrics

**Inter-trial similarity (0-1):**
- **> 0.8:** Very similar descriptions across trials
- **0.6-0.8:** Moderately similar
- **< 0.6:** Descriptions differ significantly

**Average PC1 variance:**
- **> 0.5:** Descriptions align along one main dimension
- **0.3-0.5:** Moderate consistency
- **< 0.3:** Highly varied descriptions

## Advanced Usage

### Custom Embedding Models

```python
# Use a different sentence transformer model
prober = EmbeddingProber(model_name='all-mpnet-base-v2')  # More accurate
prober = EmbeddingProber(model_name='paraphrase-MiniLM-L3-v2')  # Faster
```

### Analyzing Specific Objects

```python
# Analyze only specific objects
df_filtered = df[df['object_id'].isin(['1A_A', '2B_B', '3C_C'])]
prober.generate_embeddings(df_filtered)
```

### Comparing Human vs. ChatGPT

```python
comparator = TrialComparator()

# Load ChatGPT descriptions
comparator.load_trial_data('ChatGPT_Trial3', 'chatgpt.xlsx', 
                          text_column='chatgpt response - description')

# Load human descriptions  
comparator.load_trial_data('Human_Descriptions', 'human.xlsx',
                          text_column='human written description')

# Compare
comparator.visualize_trial_comparison()
```

### Extracting Specific Features

```python
# After running PCA, extract loadings for specific analysis
for obj_id, pca_data in prober.pca_results.items():
    pc1_loadings = pca_data['transformed'][:, 0]
    
    # Find descriptions that emphasize dimension 1
    high_pc1 = [i for i, loading in enumerate(pc1_loadings) if loading > 0.5]
    
    print(f"Object {obj_id}:")
    print(f"  High PC1 descriptions: {high_pc1}")
```

## Adapting for Your Study

To replicate the http://stanford-cogsci.org:3020/ study format:

1. **Collect descriptions** from Prolific participants
2. **Save to Excel** with same format as ChatGPT data
3. **Run comparison:**
   ```python
   comparator.load_trial_data('Prolific_Participants', 'prolific_data.xlsx')
   comparator.load_trial_data('ChatGPT_Baseline', 'chatgpt_data.xlsx')
   ```
4. **Analyze differences** in semantic dimensions

## Integration with ShapeBias-VLM

This code is designed to complement the [ShapeBias-VLM](https://github.com/SamahAbdelrahim/ShapeBias-VLM) repository:

```python
# After running embedding analysis, export for shape bias analysis
import json

with open('semantic_analysis_results.json', 'r') as f:
    results = json.load(f)

# Extract features for each object
features = {}
for obj_id, analysis in results.items():
    features[obj_id] = {
        'pc1_variance': analysis['explained_variance'][0],
        'n_dimensions': len(analysis['explained_variance']),
        'total_variance_3pc': sum(analysis['explained_variance'][:3])
    }

# Save for downstream analysis
with open('shape_bias_features.json', 'w') as f:
    json.dump(features, f, indent=2)
```

## Troubleshooting

**Issue:** "RuntimeError: Couldn't load model"
- **Solution:** Check internet connection, model downloads on first use

**Issue:** Not enough descriptions for PCA
- **Solution:** Need at least 2 descriptions per object, preferably 5+

**Issue:** All variance in PC1
- **Solution:** Normal if descriptions are very consistent, check if they're too similar

## Citation

If you use this code, please cite:
- The sentence-transformers library
- Your lab's paper (when published)

## Contact

For questions about this analysis pipeline, contact the LangCog Lab at Stanford.

## Next Steps (Your TODOs)

Based on your lab notes:

- [x] Implement embedding-based probing
- [ ] Run on Trial 1, 2, and 3 data
- [ ] Compare results across trials
- [ ] Collect human descriptions via Prolific
- [ ] Compare ChatGPT vs. Human semantic dimensions
- [ ] Analyze: Do ChatGPT and humans use similar semantic axes?
- [ ] Investigate memory effects between trials
