"""
Multi-Trial Comparison Script
Compares embeddings across different ChatGPT trials and human data
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from typing import Dict, List


class TrialComparator:
    """Compare embeddings across different trials and conditions"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.trial_embeddings = {}
        self.trial_metadata = {}
    
    def load_trial_data(self, trial_name: str, excel_path: str, 
                       text_column='chatgpt response - description') -> pd.DataFrame:
        """Load data for a specific trial"""
        print(f"\nLoading {trial_name} from {excel_path}")
        df = pd.read_excel(excel_path)
        
        # Create object ID
        df['object_id'] = df['object number'].astype(str) + '_' + df['object letter'].astype(str)
        df = df[df[text_column].notna()].copy()
        
        # Store embeddings
        descriptions = df[text_column].tolist()
        embeddings = self.model.encode(descriptions, show_progress_bar=True)
        
        self.trial_embeddings[trial_name] = {
            'embeddings': embeddings,
            'descriptions': descriptions,
            'object_ids': df['object_id'].tolist(),
            'df': df
        }
        
        self.trial_metadata[trial_name] = {
            'n_descriptions': len(descriptions),
            'n_objects': df['object_id'].nunique()
        }
        
        print(f"Loaded {len(descriptions)} descriptions for {df['object_id'].nunique()} objects")
        return df
    
    def compute_trial_similarity(self) -> Dict:
        """Compute similarity between trials"""
        print("\nComputing inter-trial similarity...")
        
        trial_names = list(self.trial_embeddings.keys())
        similarity_matrix = np.zeros((len(trial_names), len(trial_names)))
        
        for i, trial1 in enumerate(trial_names):
            for j, trial2 in enumerate(trial_names):
                emb1 = self.trial_embeddings[trial1]['embeddings']
                emb2 = self.trial_embeddings[trial2]['embeddings']
                
                # Average cosine similarity between all pairs
                sim = cosine_similarity(emb1, emb2)
                similarity_matrix[i, j] = np.mean(sim)
        
        return {
            'trial_names': trial_names,
            'similarity_matrix': similarity_matrix.tolist()
        }
    
    def compare_semantic_dimensions(self, n_components=5) -> Dict:
        """
        Compare principal components across trials to see if semantic
        dimensions are consistent
        """
        print("\nComparing semantic dimensions across trials...")
        
        results = {}
        
        for trial_name, data in self.trial_embeddings.items():
            # Group by object
            embeddings_by_obj = {}
            for emb, obj_id in zip(data['embeddings'], data['object_ids']):
                if obj_id not in embeddings_by_obj:
                    embeddings_by_obj[obj_id] = []
                embeddings_by_obj[obj_id].append(emb)
            
            # PCA for each object
            trial_pca = {}
            for obj_id, embs in embeddings_by_obj.items():
                if len(embs) < 2:
                    continue
                
                embs_array = np.array(embs)
                n_comp = min(n_components, len(embs) - 1)
                pca = PCA(n_components=n_comp)
                pca.fit(embs_array)
                
                trial_pca[obj_id] = {
                    'explained_variance': pca.explained_variance_ratio_.tolist(),
                    'n_components': n_comp,
                    'n_descriptions': len(embs)
                }
            
            results[trial_name] = trial_pca
        
        return results
    
    def visualize_trial_comparison(self, output_dir='comparison_figures'):
        """Create visualizations comparing trials"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\nGenerating comparison visualizations in {output_dir}/...")
        
        # 1. t-SNE visualization of all trials
        self._plot_tsne_comparison(output_path)
        
        # 2. Similarity heatmap
        self._plot_similarity_heatmap(output_path)
        
        # 3. Variance explained comparison
        self._plot_variance_comparison(output_path)
    
    def _plot_tsne_comparison(self, output_path: Path):
        """t-SNE plot showing all trials together"""
        # Combine all embeddings
        all_embeddings = []
        all_labels = []
        all_trials = []
        
        for trial_name, data in self.trial_embeddings.items():
            all_embeddings.append(data['embeddings'])
            all_labels.extend(data['object_ids'])
            all_trials.extend([trial_name] * len(data['embeddings']))
        
        all_embeddings = np.vstack(all_embeddings)
        
        # Run t-SNE
        print("Running t-SNE (this may take a moment)...")
        tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, len(all_embeddings)-1))
        embeddings_2d = tsne.fit_transform(all_embeddings)
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for trial_name in self.trial_embeddings.keys():
            mask = np.array(all_trials) == trial_name
            ax.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1],
                      label=trial_name, alpha=0.6, s=50)
        
        ax.set_xlabel('t-SNE Dimension 1')
        ax.set_ylabel('t-SNE Dimension 2')
        ax.set_title('t-SNE Visualization of All Trials')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'tsne_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_similarity_heatmap(self, output_path: Path):
        """Heatmap showing similarity between trials"""
        sim_results = self.compute_trial_similarity()
        
        fig, ax = plt.subplots(figsize=(8, 7))
        
        sns.heatmap(sim_results['similarity_matrix'],
                   xticklabels=sim_results['trial_names'],
                   yticklabels=sim_results['trial_names'],
                   annot=True, fmt='.3f', cmap='YlOrRd',
                   ax=ax, cbar_kws={'label': 'Average Cosine Similarity'})
        
        ax.set_title('Inter-Trial Similarity Matrix')
        plt.tight_layout()
        plt.savefig(output_path / 'trial_similarity_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_variance_comparison(self, output_path: Path):
        """Compare variance explained across trials"""
        semantic_dims = self.compare_semantic_dimensions()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # For each trial, compute average variance explained by PC1
        trial_names = []
        pc1_variances = []
        
        for trial_name, objects in semantic_dims.items():
            trial_names.append(trial_name)
            pc1_vars = [obj['explained_variance'][0] for obj in objects.values() 
                       if len(obj['explained_variance']) > 0]
            pc1_variances.append(np.mean(pc1_vars) if pc1_vars else 0)
        
        ax.bar(trial_names, pc1_variances)
        ax.set_ylabel('Average Variance Explained by PC1')
        ax.set_title('Semantic Coherence Across Trials\n(Higher = More Consistent Descriptions)')
        ax.set_ylim(0, 1)
        
        # Add value labels on bars
        for i, v in enumerate(pc1_variances):
            ax.text(i, v + 0.02, f'{v:.2%}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(output_path / 'variance_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_comparison_report(self, output_file='trial_comparison_report.txt'):
        """Generate a text report comparing trials"""
        print(f"\nGenerating comparison report: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("TRIAL COMPARISON REPORT\n")
            f.write("="*80 + "\n\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-"*80 + "\n")
            for trial_name, metadata in self.trial_metadata.items():
                f.write(f"\n{trial_name}:\n")
                f.write(f"  Total descriptions: {metadata['n_descriptions']}\n")
                f.write(f"  Unique objects: {metadata['n_objects']}\n")
            
            # Similarity analysis
            f.write("\n" + "="*80 + "\n")
            f.write("INTER-TRIAL SIMILARITY\n")
            f.write("-"*80 + "\n")
            
            sim_results = self.compute_trial_similarity()
            trial_names = sim_results['trial_names']
            sim_matrix = np.array(sim_results['similarity_matrix'])
            
            for i, trial1 in enumerate(trial_names):
                for j, trial2 in enumerate(trial_names):
                    if i < j:
                        f.write(f"{trial1} vs {trial2}: {sim_matrix[i,j]:.3f}\n")
            
            # Semantic dimension analysis
            f.write("\n" + "="*80 + "\n")
            f.write("SEMANTIC DIMENSION ANALYSIS\n")
            f.write("-"*80 + "\n")
            
            semantic_dims = self.compare_semantic_dimensions()
            
            for trial_name, objects in semantic_dims.items():
                f.write(f"\n{trial_name}:\n")
                pc1_vars = [obj['explained_variance'][0] for obj in objects.values()]
                f.write(f"  Average PC1 variance: {np.mean(pc1_vars):.2%}\n")
                f.write(f"  Objects analyzed: {len(objects)}\n")
        
        print(f"Report saved to {output_file}")


def main():
    """Example usage"""
    
    comparator = TrialComparator()
    
    # Load Trial 3 (this is the data you provided)
    excel_path = '/mnt/user-data/uploads/chatgpt_generated_responses_and_images.xlsx'
    comparator.load_trial_data('Trial_3', excel_path)
    
    # If you have other trials, load them too:
    # comparator.load_trial_data('Trial_1', 'path/to/trial1.xlsx')
    # comparator.load_trial_data('Trial_2', 'path/to/trial2.xlsx')
    # comparator.load_trial_data('Human_Data', 'path/to/human.xlsx')
    
    # Generate visualizations
    comparator.visualize_trial_comparison('comparison_figures')
    
    # Generate report
    comparator.generate_comparison_report('trial_comparison_report.txt')
    
    print("\nComparison analysis complete!")


if __name__ == "__main__":
    main()
