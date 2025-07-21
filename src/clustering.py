import os
import torch
import numpy as np
import traceback
import json
import pandas as pd

from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from sentence_transformers import SentenceTransformer
from src.logger import setup_logger
from src.models import Post
import src.storage as storage

logger = setup_logger("Analysis-Service")

# Create embeddings directory if it doesn't exist
emb_dir = "embeddings/"
if not os.path.isdir(emb_dir):
    os.makedirs(emb_dir)

DEFAULT_EMB_MODEL = "all-mpnet-base-v2"

class Clustering:
    def __init__(self, posts, comments, embeddings_file):
        self.posts = posts
        if isinstance(posts, list):
            self.posts = pd.DataFrame(posts)
        else:
            self.posts = posts
        self.comments = comments
        self.embeddings_file = embeddings_file
        if not os.path.exists(self.embeddings_file):
            self.embeddings = None
        else:
            self.embeddings = np.load(self.embeddings_file) if os.path.exists(self.embeddings_file) else None

    def _run(self):
        logger.info("Starting clustering...")
        if self.embeddings is None:
            self.embeddings = self.create_embeddings(self.posts["top_comments"], save_path=self.embeddings_file)
        
        hdbscan_clusters = self.create_hdbscan_clusters(self.embeddings)
        self.posts['cluster_labels'] = hdbscan_clusters
        self.posts = [
            Post(**{**row, "cluster_labels": row["cluster_labels"]})
            for row in self.posts.to_dict(orient="records")
        ]
        logger.info("Clustering completed. Saving results...")
        # Save posts with clusters
        storage.save_csv(self.posts)
        storage.save_json(self.posts)
        storage.save_sqlite(self.posts)

        logger.info("Clustering completed.")

    def create_embeddings(self, text_to_embed: str | list[str], save_path: str = "reddit_posts_mpnet", model: str = DEFAULT_EMB_MODEL, overwrite: bool = False):
        """
        This function creates embeddings from 'text_to_embed'.
        """
        logger.info("Starting the embedding creation...")
        output_path = emb_dir+save_path

        if not os.path.isdir(output_path) or overwrite is True:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                loaded_model = SentenceTransformer(
                        model,
                        device=device
                    )
                
                embeddings = loaded_model.encode(text_to_embed, show_progress_bar=True)
                np.save(output_path, embeddings)
                
                logger.info("Embeddings created and saved in %s", save_path)
                return embeddings

            except Exception as e:
                logger.error("Error creating embeddings: %s", str(e))
                logger.error(traceback.format_exc())

        logger.info("Embeddings file already exists and overwrite is set to False. Skipping embeddings creation...")
        return 

    def reduce_embeddings_dimensionality(self, embeddings: np.ndarray, n_components: int = 50):
        """
        This function reduces the dimensionality of embeddings using PCA.
        """
        logger.info("Reducing embeddings dimensionality...")
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(embeddings)

            pca = PCA(n_components=n_components)
            X_reduced = pca.fit_transform(X_scaled)

            logger.info("Embeddings dimensionality reduced to %d components", n_components)
            return X_reduced

        except Exception as e:
            logger.error("Error reducing embeddings dimensionality: %s", str(e))
            logger.error(traceback.format_exec())
            return None

    def create_hdbscan_clusters(
            self,
            embeddings: np.ndarray,
            min_cluster_size: int = 10, min_samples: int = 5,
            metric: str = 'euclidean'
        ) -> np.ndarray:
        """
        This function creates HDBSCAN clusters from the embeddings.
        """        
        logger.info("Running HDBSCAN clustering...")
        if embeddings is None:
            logger.error("Embeddings not supplied. Cannot run HDBSCAN.")
            return None
        try:
            reduced_embs = self.reduce_embeddings_dimensionality(embeddings)
            clusterer = HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric=metric
            )
            labels = clusterer.fit_predict(reduced_embs)
            logger.info("HDBSCAN clustering completed with %d clusters", len(set(labels)) - (1 if -1 in labels else 0))
        except Exception as e:
            logger.error("Error running HDBSCAN: %s", str(e))

        return labels
        
# Optional: Run grid search for HDBSCAN parameters
def grid_search_hdbscan(dim_reduced_embeddings: np.ndarray, plot_results: bool = True):
    """
    Optionally, you can implement a grid search for HDBSCAN parameters.
    From experiments, we found that min_cluster_size=10 and min_samples=5 often yield good results.
    """
    import seaborn as sns
    import matplotlib.pyplot as plt
    import pandas as pd

    logger.info("Starting HDBSCAN grid search...")
    results = []

    for min_cluster_size in [5, 10, 15, 20]:
        for min_samples in [None, 5, 10]:
            clusterer = HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples if min_samples else min_cluster_size,
                metric='euclidean'
            )
            cluster_labels = clusterer.fit_predict(dim_reduced_embeddings)

            # Calculate cluster statistics
            n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            n_noise = list(cluster_labels).count(-1)
            cluster_sizes = pd.Series(cluster_labels).value_counts()
            largest = cluster_sizes.max()
            median = cluster_sizes.median()
            mean = cluster_sizes[cluster_sizes.index != -1].mean()

            results.append({
                "min_cluster_size": min_cluster_size,
                "min_samples": min_samples,
                "n_clusters": n_clusters,
                "n_noise": n_noise,
                "largest": largest,
                "median": median,
                "mean": mean
            })
    with open("hdbscan_results.json", "w") as f:
        json.dump(results, f, indent=4)

    logger.info("HDBSCAN grid search completed. Results saved to hdbscan_results.json")
    if plot_results:
        try:
            os.makedirs("analysis_results", exist_ok=True)

            df = pd.DataFrame(results)
            plt.figure(figsize=(12, 6))
            sns.lineplot(data=df, x="min_cluster_size", y="n_clusters")
            plt.xlabel('Min Cluster Size')
            plt.ylabel('Number of Clusters')
            plt.title("HDBSCAN Clusters Grid Search Results")
            plt.savefig("analysis_results/hdbscan_clusters_vs_min_cluster_size.png")
            plt.show()
        except Exception as e:
            logger.error("Error occurred while plotting HDBSCAN results: %s", str(e))
    return results