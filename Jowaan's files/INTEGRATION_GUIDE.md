# Integration with ShapeBias-VLM Repository

This guide shows how to integrate the embedding-based probing analysis with your existing [ShapeBias-VLM](https://github.com/SamahAbdelrahim/ShapeBias-VLM) codebase.

## Repository Structure

```
your-project/
├── ShapeBias-VLM/                 # Your existing repository
│   ├── familiar_objects/
│   ├── experiments/
│   └── ...
├── embedding-probing/             # New analysis code (this toolkit)
│   ├── embedding_probing_analysis.py
│   ├── trial_comparison.py
│   ├── requirements.txt
│   └── README.md
├── data/
│   ├── trial1/
│   │   └── chatgpt_responses_trial1.xlsx
│   ├── trial2/
│   │   └── chatgpt_responses_trial2.xlsx
│   ├── trial3/
│   │   └── chatgpt_responses_trial3.xlsx
│   └── human/
│       └── prolific_descriptions.xlsx
└── results/
    ├── embeddings/
    ├── visualizations/
    └── comparisons/
```

## Step-by-Step Integration

### 1. Clone and Setup

```bash
# Clone the ShapeBias-VLM repository
git clone https://github.com/SamahAbdelrahim/ShapeBias-VLM.git
cd ShapeBias-VLM

# Create a new directory for embedding analysis
mkdir -p embedding-probing
cd embedding-probing

# Copy the analysis scripts here
# (embedding_probing_analysis.py, trial_comparison.py, etc.)

# Install dependencies
pip install -r requirements.txt --break-system-packages
```

### 2. Organize Your Data

Create a consistent data structure:

```bash
mkdir -p ../data/{trial1,trial2,trial3,human}
```

Each Excel file should have the same columns:
- `object number`
- `object letter`
- `chatgpt response - description` (or `human written description`)
- `video link` (optional)

### 3. Run Complete Analysis Pipeline

```python
# complete_analysis.py
"""
Complete embedding-based probing pipeline for all trials and human data
"""

from embedding_probing_analysis import EmbeddingProber
from trial_comparison import TrialComparator
import pandas as pd
from pathlib import Path

# Configuration
DATA_DIR = Path('../data')
RESULTS_DIR = Path('../results')
RESULTS_DIR.mkdir(exist_ok=True)

# Initialize
prober = EmbeddingProber(model_name='all-MiniLM-L6-v2')
comparator = TrialComparator(model_name='all-MiniLM-L6-v2')

print("="*80)
print("COMPLETE EMBEDDING-BASED PROBING ANALYSIS")
print("="*80)

# ============================================================================
# PART 1: Individual Trial Analysis
# ============================================================================

trials = {
    'Trial_1_Memory_ON': DATA_DIR / 'trial1' / 'chatgpt_responses_trial1.xlsx',
    'Trial_2_Memory_ON': DATA_DIR / 'trial2' / 'chatgpt_responses_trial2.xlsx',
    'Trial_3_Memory_OFF': DATA_DIR / 'trial3' / 'chatgpt_responses_trial3.xlsx',
    'Human_Prolific': DATA_DIR / 'human' / 'prolific_descriptions.xlsx',
}

for trial_name, trial_path in trials.items():
    if not trial_path.exists():
        print(f"\n⚠️  {trial_name} data not found at {trial_path}, skipping...")
        continue
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {trial_name}")
    print('='*80)
    
    # Load and analyze
    df = prober.load_data(str(trial_path))
    prober.generate_embeddings(df)
    prober.perform_pca_analysis(n_components=5)
    
    # Get results
    analysis_results = prober.analyze_semantic_dimensions(df)
    
    # Save results
    results_file = RESULTS_DIR / 'embeddings' / f'{trial_name}_analysis.json'
    results_file.parent.mkdir(exist_ok=True)
    prober.save_results(analysis_results, str(results_file))
    
    # Create visualizations
    viz_dir = RESULTS_DIR / 'visualizations' / trial_name
    prober.visualize_results(str(viz_dir))
    
    print(f"✓ Results saved to {results_file}")
    print(f"✓ Visualizations saved to {viz_dir}")

# ============================================================================
# PART 2: Cross-Trial Comparison
# ============================================================================

print(f"\n{'='*80}")
print("CROSS-TRIAL COMPARISON")
print('='*80)

# Load all trials into comparator
for trial_name, trial_path in trials.items():
    if trial_path.exists():
        comparator.load_trial_data(trial_name, str(trial_path))

# Generate comparisons
comparison_dir = RESULTS_DIR / 'comparisons'
comparator.visualize_trial_comparison(str(comparison_dir))
comparator.generate_comparison_report(str(comparison_dir / 'comparison_report.txt'))

print(f"✓ Comparison visualizations saved to {comparison_dir}")

# ============================================================================
# PART 3: Export for Shape Bias Analysis
# ============================================================================

print(f"\n{'='*80}")
print("EXPORTING FEATURES FOR SHAPE BIAS ANALYSIS")
print('='*80)

# Prepare features for shape bias experiments
import json

shape_bias_features = {}

for trial_name, trial_path in trials.items():
    if not trial_path.exists():
        continue
    
    results_file = RESULTS_DIR / 'embeddings' / f'{trial_name}_analysis.json'
    if results_file.exists():
        with open(results_file, 'r') as f:
            trial_results = json.load(f)
        
        shape_bias_features[trial_name] = {}
        
        for obj_id, obj_analysis in trial_results.items():
            if 'explained_variance' in obj_analysis:
                shape_bias_features[trial_name][obj_id] = {
                    'pc1_variance': obj_analysis['explained_variance'][0],
                    'pc2_variance': obj_analysis['explained_variance'][1] if len(obj_analysis['explained_variance']) > 1 else 0,
                    'n_dimensions': len(obj_analysis['explained_variance']),
                    'cumulative_variance_3pc': sum(obj_analysis['explained_variance'][:3]),
                    'n_descriptions': obj_analysis['n_descriptions']
                }

# Save for downstream analysis
export_file = RESULTS_DIR / 'shape_bias_features.json'
with open(export_file, 'w') as f:
    json.dump(shape_bias_features, f, indent=2)

print(f"✓ Shape bias features exported to {export_file}")

print("\n" + "="*80)
print("✓ COMPLETE ANALYSIS FINISHED")
print("="*80)
print(f"\nResults saved in: {RESULTS_DIR}/")
print(f"  - Individual analyses: {RESULTS_DIR / 'embeddings'}/")
print(f"  - Visualizations: {RESULTS_DIR / 'visualizations'}/")
print(f"  - Comparisons: {RESULTS_DIR / 'comparisons'}/")
print(f"  - Shape bias export: {export_file}")
```

### 4. Link with Web Experiment

To replicate http://stanford-cogsci.org:3020/ for collecting human data:

```python
# web_experiment_integration.py
"""
Integration with Prolific/web experiment data collection
"""

import pandas as pd
from pathlib import Path

def prepare_prolific_data(response_file: str, output_file: str):
    """
    Convert Prolific responses to standard format for analysis
    
    Args:
        response_file: CSV from Prolific with columns:
            - participant_id
            - object_video_url
            - description_text
            - timestamp
        output_file: Output Excel file in standard format
    """
    
    # Load Prolific data
    df = pd.read_csv(response_file)
    
    # Parse object IDs from video URLs
    # Assuming URLs like: .../videos/1A.mp4
    df['object_number'] = df['object_video_url'].str.extract(r'/(\d+)[A-Z]\.mp4')
    df['object_letter'] = df['object_video_url'].str.extract(r'/\d+([A-Z])\.mp4')
    
    # Rename columns to standard format
    df_standard = pd.DataFrame({
        'object number': df['object_number'],
        'object letter': df['object_letter'],
        'video link': df['object_video_url'],
        'human written description': df['description_text'],
        'participant_id': df['participant_id'],
        'timestamp': df['timestamp']
    })
    
    # Save to Excel
    df_standard.to_excel(output_file, index=False)
    print(f"✓ Converted {len(df_standard)} responses to {output_file}")
    
    return df_standard

# Example usage:
# prepare_prolific_data('prolific_responses.csv', '../data/human/prolific_descriptions.xlsx')
```

### 5. Analysis Workflow

Complete workflow from data collection to results:

```bash
# 1. Collect ChatGPT descriptions (Trials 1, 2, 3)
#    Save to data/trial1/, data/trial2/, data/trial3/

# 2. Collect human descriptions via Prolific
python web_experiment_integration.py

# 3. Run complete analysis
python complete_analysis.py

# 4. Review results
# - Check results/visualizations/ for plots
# - Read results/comparisons/comparison_report.txt
# - Use results/shape_bias_features.json for further analysis

# 5. Generate paper figures
python generate_paper_figures.py  # Create publication-ready plots
```

### 6. Key Analysis Questions

Use the results to answer:

**Memory Effects:**
```python
# Compare Trial 1 vs Trial 2 (both memory ON) vs Trial 3 (memory OFF)
# Look at: results/comparisons/trial_similarity_heatmap.png

# Key metrics:
# - Are Trial 1 and Trial 2 more similar to each other?
# - Does Trial 3 show different semantic patterns?
# - Check PC1 variance: Does memory increase consistency?
```

**Human vs. ChatGPT:**
```python
# Compare Human vs all ChatGPT trials
# Look at: results/comparisons/tsne_comparison.png

# Key questions:
# - Do human descriptions cluster separately?
# - Which ChatGPT trial is most similar to humans?
# - What semantic dimensions differ?
```

**Semantic Structure:**
```python
# For each object, check results/embeddings/[trial]_analysis.json

# Key patterns to look for:
# - High PC1 variance = diverse descriptions
# - Low PC1 variance = consistent emphasis
# - PC1 interpretation: shape vs. material vs. color?
# - Are patterns consistent across objects?
```

## Next Steps

1. **Collect Remaining Data**
   - [ ] Trial 1 with memory ON
   - [ ] Trial 2 with memory ON
   - [ ] Human data via Prolific

2. **Run Analysis**
   - [ ] Individual trial analyses
   - [ ] Cross-trial comparisons
   - [ ] Extract semantic dimensions

3. **Interpret Results**
   - [ ] Does memory affect ChatGPT descriptions?
   - [ ] How do ChatGPT and humans differ?
   - [ ] What features do descriptions emphasize?

4. **Publication**
   - [ ] Create publication-quality figures
   - [ ] Write results section
   - [ ] Include statistical comparisons

## Troubleshooting

**Issue:** Different objects have different numbers of descriptions
- **Solution:** PCA handles this automatically, skips objects with <2 descriptions

**Issue:** Some trials missing
- **Solution:** Analysis skips missing files, processes what's available

**Issue:** Memory errors with large datasets
- **Solution:** Process trials individually, then combine results

## Contact

Questions about integration? Contact the LangCog Lab or open an issue in the GitHub repository.
