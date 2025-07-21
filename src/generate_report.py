import matplotlib.pyplot as plt
import pandas as pd
import os

from sklearn.feature_extraction.text import CountVectorizer
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from src.logger import setup_logger

logger = setup_logger("Report-")

class ReportGenerator:
    def __init__(self, posts, template_dir="templates", output_dir="reports"):
        self.posts = posts
        self.template_dir = template_dir
        self.output_dir = output_dir+"/"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs(self.output_dir, exist_ok=True)
        self.clusters = []
        self.flagged_users = []

        if isinstance(posts, list):
            self.posts = pd.DataFrame([p.__dict__ for p in posts])
        else:
            self.posts = posts

    def summarize_clusters(self):
        clusters = []
        try:
            for c in sorted(self.posts['cluster_labels'].dropna().unique()):
                if c == -1:
                    continue
                cluster_posts = self.posts[self.posts['cluster_labels'] == c]
                texts = (cluster_posts['title'].fillna('') + " " + cluster_posts['selftext'].fillna('')).tolist()
                vec = CountVectorizer(stop_words="english", max_features=10)
                vec.fit(texts)
                keywords = vec.get_feature_names_out()

                # LLM/Narrative summary (placeholder) TBD
                # if llm:
                sample_text = "\n".join(cluster_posts['title'].head(5).tolist())

                top_authors = cluster_posts['author'].value_counts().head(3).index.tolist()
                sample_posts = cluster_posts['title'].sample(min(5, len(cluster_posts))).tolist()

                timeline_name = f"timeline_cluster_{c}.png"
                timeline_path = f"{self.output_dir}/{timeline_name}"
                cluster_posts['created_utc'].dt.date.value_counts().sort_index().plot(kind="bar", figsize=(6,2))
                plt.title(f"Cluster {c} Timeline")
                plt.tight_layout()
                plt.savefig(timeline_path)
                plt.close()

                clusters.append({
                    "id": c,
                    "keywords": keywords,
                    "sample_text": sample_text,
                    "size": len(cluster_posts),
                    "top_authors": top_authors,
                    "sample_posts": sample_posts,
                    "timeline_plot": timeline_name,
                    "flagged": False,
                })
            self.clusters = clusters
        except TypeError as e:
            logger.error(f"Error summarizing clusters: {str(e)}")
            logger.error("Ensure 'cluster_labels' column exists and is not empty")
            self.clusters = []
        except Exception as e:
            logger.error(f"Unexpected error summarizing clusters: {str(e)}")
            self.clusters = []

    # TODO: Expand this with more sophisticated heuristics
    def flag_suspicious(self):
        # Cluster-level flags
        for cluster in self.clusters:
            cluster_posts = self.posts[self.posts['cluster_labels'] == cluster["id"]]
            author_counts = cluster_posts["author"].value_counts()
            burst = (cluster_posts['created_utc'].max() - cluster_posts['created_utc'].min()).total_seconds() < 3600 # 1 hour burst
            high_overlap = (author_counts > 4).sum() > 0 # Flag if more than 4 authors in a short time span
            if burst or high_overlap:
                cluster["flagged"] = True

        try:
            # User-level flags
            user_clusters = self.posts.groupby("author")["cluster_labels"].nunique()
            self.flagged_users = user_clusters[user_clusters > 1].index.tolist()
        except AttributeError as e:
            logger.error(f"Error flagging suspicious users: {str(e)}")
            logger.error("Ensure 'cluster_labels' column exists and is not empty")
            self.flagged_users = []
        except Exception as e:
            logger.error(f"Unexpected error flagging users: {str(e)}")
            self.flagged_users = []

    def render_html(self):
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template('report_template.html')
        html = template.render(
            clusters=self.clusters,
            flagged_users=self.flagged_users,
            total_posts=len(self.posts)
        )
        with open(f"{self.output_dir}/report.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Report generated at {self.output_dir}/report.html")

    def run(self):
        self.summarize_clusters()
        self.flag_suspicious()
        self.render_html()

