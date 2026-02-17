# Quick Start Guide

## What You Have

A complete embedding-based probing toolkit for analyzing object descriptions from ChatGPT and humans.

## Files Included

### Core Analysis Scripts
1. **embedding_probing_analysis.py** - Main analysis script for single trials
2. **trial_comparison.py** - Compare multiple trials and conditions
3. **demo_analysis_workflow.py** - Demonstrates the analysis without requiring dependencies

### Documentation
4. **README.md** - Comprehensive usage guide
5. **INTEGRATION_GUIDE.md** - Integration with ShapeBias-VLM repository
6. **requirements.txt** - Python dependencies

## 3-Minute Quick Start

### For Your Current Data (Trial 3)

```bash
# 1. Install dependencies
pip install sentence-transformers pandas numpy scikit-learn matplotlib seaborn openpyxl --break-system-packages

# 2. Run analysis
python embedding_probing_analysis.py

# 3. Check results
ls output_figures/           # Visualizations
cat semantic_analysis_results.json | head -50  # Analysis results
```

### For Multiple Trials Comparison

```bash
# 1. Edit trial_comparison.py to add your trial data paths
# 2. Run comparison
python trial_comparison.py

# 3. Check results
ls comparison_figures/
cat trial_comparison_report.txt
```

## What This Does

**Embedding-Based Probing** = Finding the main "axes" along which descriptions vary

**Example:**
- Some people describe objects by SHAPE: "cylindrical," "rounded," "compact"
- Others describe by MATERIAL: "paper," "textured," "crinkled"
- PCA finds that the main difference (PC1) is shape vs. material emphasis

## Your Research Questions

✓ **Does memory affect ChatGPT?**
  - Compare Trial 1 & 2 (memory ON) vs Trial 3 (memory OFF)
  - Check if semantic dimensions shift

✓ **ChatGPT vs. Humans?**
  - Compare embedding similarity
  - See if they use same semantic axes

✓ **What features matter?**
  - PCA reveals dominant dimensions
  - Shape vs. material? Color vs. texture? Global vs. local?

## Expected Results

**semantic_analysis_results.json:**
```json
{
  "1A_A": {
    "n_descriptions": 5,
    "explained_variance": [0.65, 0.20, 0.10, 0.03, 0.02],
    "components": {
      "PC1": {
        "variance_explained": 0.65,
        "high_loading_descriptions": ["focused on texture..."],
        "low_loading_descriptions": ["focused on shape..."]
      }
    }
  }
}
```

**Visualizations:**
- `variance_explained.png` - Shows dimensionality of descriptions
- `pca_[object].png` - Scatter plots for each object
- `tsne_comparison.png` - All trials visualized together
- `trial_similarity_heatmap.png` - Similarity matrix

## Key Insights to Look For

1. **High PC1 Variance (>50%)**
   - Descriptions vary along one main dimension
   - Example: Some talk about shape, others about material

2. **Low PC1 Variance (<30%)**
   - Descriptions are multidimensional
   - Multiple unrelated features emphasized

3. **Similar Across Trials**
   - Memory doesn't affect semantic structure
   - ChatGPT consistent in how it varies

4. **Different Across Trials**
   - Memory changes emphasis
   - Trial 3 focuses on different features

## Next Steps

1. ✓ You have Trial 3 data analyzed (via demo)
2. Get Trial 1 & 2 data
3. Collect human data via Prolific
4. Run `trial_comparison.py` to compare all
5. Interpret results for your paper

## Questions?

- Check README.md for detailed documentation
- Check INTEGRATION_GUIDE.md for GitHub integration
- Run demo_analysis_workflow.py to see expected output

## One-Line Summary

This code finds the main "semantic dimensions" (like shape vs. material) in object descriptions and compares them across different ChatGPT trials and human responses.
