"""
Embedding-Based Probing for Object Descriptions
Analyzes semantic structure in ChatGPT and human-generated object descriptions

Based on the approach from:
- Embed each description
- PCA/factor analysis within each object
- Identify dominant semantic directions
- Compare across models and trials
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class EmbeddingProber:
    """Analyzes semantic structure in object descriptions using embeddings"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the embedding prober
        
        Args:
            model_name: HuggingFace sentence-transformer model name
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embeddings = {}
        self.pca_results = {}
        
    def load_data(self, excel_path: str) -> pd.DataFrame:
        """Load and preprocess the Excel data"""
        print(f"\nLoading data from: {excel_path}")
        df = pd.read_excel(excel_path)
        
        # Clean and prepare the data
        df['object_id'] = df['object number'].astype(str) + '_' + df['object letter'].astype(str)
        df = df[df['chatgpt response - description'].notna()].copy()
        
        print(f"Loaded {len(df)} descriptions for {df['object_id'].nunique()} unique objects")
        return df
    
    def generate_embeddings(self, df: pd.DataFrame, text_column='chatgpt response - description') -> Dict:
        """
        Generate embeddings for all descriptions
        
        Args:
            df: DataFrame with descriptions
            text_column: Column containing text to embed
            
        Returns:
            Dictionary mapping object_id to embeddings
        """
        print(f"\nGenerating embeddings for {len(df)} descriptions...")
        
        # Extract descriptions
        descriptions = df[text_column].tolist()
        object_ids = df['object_id'].tolist()
        
        # Generate embeddings
        embeddings = self.model.encode(descriptions, show_progress_bar=True)
        
        # Organize by object
        embeddings_by_object = {}
        for obj_id, emb in zip(object_ids, embeddings):
            if obj_id not in embeddings_by_object:
                embeddings_by_object[obj_id] = []
            embeddings_by_object[obj_id].append(emb)
        
        # Convert to arrays
        for obj_id in embeddings_by_object:
            embeddings_by_object[obj_id] = np.array(embeddings_by_object[obj_id])
        
        self.embeddings = embeddings_by_object
        print(f"Generated embeddings for {len(embeddings_by_object)} objects")
        return embeddings_by_object
    
    def perform_pca_analysis(self, n_components=5) -> Dict:
        """
        Perform PCA on embeddings for each object to find semantic dimensions
        
        Args:
            n_components: Number of principal components to extract
            
        Returns:
            Dictionary with PCA results for each object
        """
        print(f"\nPerforming PCA analysis (n_components={n_components})...")
        
        results = {}
        
        for obj_id, embs in self.embeddings.items():
            if len(embs) < 2:
                print(f"Skipping {obj_id}: only {len(embs)} description(s)")
                continue
            
            # Standardize embeddings
            scaler = StandardScaler()
            embs_scaled = scaler.fit_transform(embs)
            
            # Perform PCA
            n_comp = min(n_components, len(embs) - 1)
            pca = PCA(n_components=n_comp)
            transformed = pca.fit_transform(embs_scaled)
            
            results[obj_id] = {
                'pca': pca,
                'transformed': transformed,
                'explained_variance': pca.explained_variance_ratio_,
                'components': pca.components_,
                'n_descriptions': len(embs),
                'scaler': scaler
            }
        
        self.pca_results = results
        print(f"Completed PCA for {len(results)} objects")
        return results
    
    def analyze_semantic_dimensions(self, df: pd.DataFrame, 
                                    text_column='chatgpt response - description') -> Dict:
        """
        Analyze what each principal component represents by examining
        high-loading descriptions
        
        Args:
            df: Original DataFrame with descriptions
            text_column: Column containing descriptions
            
        Returns:
            Dictionary with analysis results
        """
        print("\nAnalyzing semantic dimensions...")
        
        analysis = {}
        
        for obj_id, pca_data in self.pca_results.items():
            # Get descriptions for this object
            obj_descs = df[df['object_id'] == obj_id][text_column].tolist()
            
            if len(obj_descs) != pca_data['n_descriptions']:
                print(f"Warning: Mismatch for {obj_id}")
                continue
            
            obj_analysis = {
                'object_id': obj_id,
                'n_descriptions': len(obj_descs),
                'explained_variance': pca_data['explained_variance'].tolist(),
                'components': {}
            }
            
            # Analyze each component
            for comp_idx in range(len(pca_data['explained_variance'])):
                loadings = pca_data['transformed'][:, comp_idx]
                
                # Get descriptions with highest and lowest loadings
                top_indices = np.argsort(loadings)[-2:][::-1]
                bottom_indices = np.argsort(loadings)[:2]
                
                obj_analysis['components'][f'PC{comp_idx+1}'] = {
                    'variance_explained': float(pca_data['explained_variance'][comp_idx]),
                    'high_loading_descriptions': [obj_descs[i] for i in top_indices if i < len(obj_descs)],
                    'low_loading_descriptions': [obj_descs[i] for i in bottom_indices if i < len(obj_descs)],
                    'loadings': loadings.tolist()
                }
            
            analysis[obj_id] = obj_analysis
        
        return analysis
    
    def visualize_results(self, output_dir='output_figures'):
        """Create visualizations of the PCA results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\nGenerating visualizations in {output_dir}/...")
        
        # 1. Variance explained plot
        self._plot_variance_explained(output_path)
        
        # 2. PCA scatter plots for each object
        self._plot_pca_scatters(output_path)
        
        print(f"Visualizations saved to {output_dir}/")
    
    def _plot_variance_explained(self, output_path: Path):
        """Plot variance explained by each component across all objects"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Collect all variance explained ratios
        all_variances = []
        object_labels = []
        
        for obj_id, data in self.pca_results.items():
            all_variances.append(data['explained_variance'])
            object_labels.append(obj_id)
        
        # Plot 1: Stacked bar chart
        n_components = max(len(v) for v in all_variances)
        variance_array = np.zeros((len(all_variances), n_components))
        
        for i, v in enumerate(all_variances):
            variance_array[i, :len(v)] = v
        
        bottom = np.zeros(len(all_variances))
        for comp in range(n_components):
            axes[0].barh(object_labels, variance_array[:, comp], left=bottom, 
                        label=f'PC{comp+1}')
            bottom += variance_array[:, comp]
        
        axes[0].set_xlabel('Cumulative Variance Explained')
        axes[0].set_title('Variance Explained by Principal Components')
        axes[0].legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        # Plot 2: Average variance explained per component
        avg_variance = np.mean(variance_array, axis=0)
        axes[1].bar(range(1, n_components+1), avg_variance)
        axes[1].set_xlabel('Principal Component')
        axes[1].set_ylabel('Average Variance Explained')
        axes[1].set_title('Average Variance Explained Across All Objects')
        axes[1].set_xticks(range(1, n_components+1))
        
        plt.tight_layout()
        plt.savefig(output_path / 'variance_explained.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_pca_scatters(self, output_path: Path):
        """Create PCA scatter plots for each object"""
        for obj_id, data in self.pca_results.items():
            if data['transformed'].shape[1] < 2:
                continue
            
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Plot PC1 vs PC2
            scatter = ax.scatter(data['transformed'][:, 0], 
                               data['transformed'][:, 1],
                               s=100, alpha=0.6, c=range(len(data['transformed'])),
                               cmap='viridis')
            
            # Add point labels
            for i in range(len(data['transformed'])):
                ax.annotate(f'{i+1}', 
                          (data['transformed'][i, 0], data['transformed'][i, 1]),
                          fontsize=8, ha='center')
            
            ax.set_xlabel(f"PC1 ({data['explained_variance'][0]:.1%} variance)")
            ax.set_ylabel(f"PC2 ({data['explained_variance'][1]:.1%} variance)")
            ax.set_title(f"PCA Projection: {obj_id}")
            ax.grid(True, alpha=0.3)
            
            plt.colorbar(scatter, label='Description Index')
            plt.tight_layout()
            
            # Save with safe filename
            safe_filename = obj_id.replace('/', '_').replace(' ', '_')
            plt.savefig(output_path / f'pca_{safe_filename}.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def compare_trials(self, trial_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Compare embeddings across different trials (e.g., Trial 1, 2, 3)
        
        Args:
            trial_data: Dictionary mapping trial names to DataFrames
            
        Returns:
            Comparison results
        """
        print("\nComparing across trials...")
        
        comparison = {}
        
        for trial_name, df in trial_data.items():
            print(f"\nProcessing {trial_name}...")
            self.generate_embeddings(df)
            self.perform_pca_analysis()
            
            comparison[trial_name] = {
                'n_objects': len(self.embeddings),
                'total_descriptions': sum(len(e) for e in self.embeddings.values()),
                'pca_results': self.pca_results.copy()
            }
        
        return comparison
    
    def save_results(self, analysis_results: Dict, output_file='analysis_results.json'):
        """Save analysis results to JSON file"""
        print(f"\nSaving results to {output_file}...")
        
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        print(f"Results saved successfully")


def main():
    """Main execution function"""
    
    # Initialize the prober
    prober = EmbeddingProber(model_name='all-MiniLM-L6-v2')
    
    # Load data
    excel_path = '/mnt/user-data/uploads/chatgpt_generated_responses_and_images.xlsx'
    df = prober.load_data(excel_path)
    
    # Generate embeddings
    prober.generate_embeddings(df)
    
    # Perform PCA analysis
    prober.perform_pca_analysis(n_components=5)
    
    # Analyze semantic dimensions
    analysis_results = prober.analyze_semantic_dimensions(df)
    
    # Save results
    prober.save_results(analysis_results, 'semantic_analysis_results.json')
    
    # Create visualizations
    prober.visualize_results('output_figures')
    
    # Print summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    for obj_id, obj_analysis in analysis_results.items():
        print(f"\n{obj_id}:")
        print(f"  Descriptions analyzed: {obj_analysis['n_descriptions']}")
        print(f"  PC1 explains: {obj_analysis['components']['PC1']['variance_explained']:.1%} of variance")
        if 'PC2' in obj_analysis['components']:
            print(f"  PC2 explains: {obj_analysis['components']['PC2']['variance_explained']:.1%} of variance")


if __name__ == "__main__":
    main()
