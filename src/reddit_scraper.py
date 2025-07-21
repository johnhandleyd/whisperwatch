import numpy as np
import praw
import os
import traceback
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

from src.models import Post, Comment
from src.utils import clean_text
from src.logger import setup_logger

logger = setup_logger("RedditScraper")

load_dotenv()

class RedditScraper:
    """
    A class to scrape Reddit posts and comments from specified subreddits.
    """
    def __init__(self,
                 subreddits,
                 top_limit=50,
                 hot_limit=50,
                 min_comments=10,
                 min_score=10,
                 max_comments_per_post=50):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="whisperwatch-script"
        )
        self.subreddits = subreddits
        self.top_limit = top_limit
        self.hot_limit = hot_limit
        self.min_comments = min_comments
        self.min_score = min_score
        self.max_comments_per_post = max_comments_per_post

        self.collected_post_ids = set()
        self.collection_date = datetime.utcnow().isoformat()
        self.posts: list[Post] = []
        self.comments: list[Comment] = []

    def _collect_post_and_comments(self, post, subreddit_name):
        logger.debug(f"Collecting post {post.id} from r/{subreddit_name}")
        try:
            if post.id in self.collected_post_ids:
                return
            self.collected_post_ids.add(post.id)

            if post.num_comments < self.min_comments or post.score < self.min_score:
                return
            
            post_obj = Post(
                post_id=post.id,
                subreddit=subreddit_name,
                author=str(post.author),
                title=clean_text(post.title),
                selftext=clean_text(post.selftext),
                score=post.score,
                num_comments=post.num_comments,
                created_utc=datetime.utcfromtimestamp(post.created_utc).isoformat(),
                flair=post.link_flair_text,
                url=post.url,
                collection_date=self.collection_date
            )
            self.posts.append(post_obj)

            post.comments.replace_more(limit=0)
            for comment in post.comments.list()[:self.max_comments_per_post]:
                comment_obj = Comment(
                    comment_id=comment.id,
                    post_id=post.id,
                    subreddit=subreddit_name,
                    author=str(comment.author),
                    body=clean_text(comment.body),
                    score=comment.score,
                    created_utc=datetime.utcfromtimestamp(comment.created_utc).isoformat(),
                    parent_id=comment.parent_id,
                    collection_date=self.collection_date
                )
                self.comments.append(comment_obj)
        except Exception as e:
            logger.error(f"Error collecting post {post.id} from r/{subreddit_name}: {str(e)}")
            logger.error(traceback.format_exc())

    def add_top_comments(self, posts, comments, n=10):
        # Convert to DataFrame if needed
        if not isinstance(posts, pd.DataFrame):
            posts_df = pd.DataFrame([p.__dict__ for p in posts])
        else:
            posts_df = posts
        if not isinstance(comments, pd.DataFrame):
            comments_df = pd.DataFrame([c.__dict__ for c in comments])
        else:
            comments_df = comments
            
        # Clean junk and compute score_len
        comments_df = comments_df[~comments_df["body"].isin(["[deleted]", "[removed]"])]
        comments_df["score_len"] = comments_df["score"] * comments_df["body"].str.len().apply(lambda x: np.log1p(x))

        # Get top comments by post_id
        top_comments_by_post = (
            comments_df
            .sort_values("score_len", ascending=False)
            .groupby("post_id")["body"]
            .apply(lambda s: s.head(n).tolist())
        )

        # Map to posts
        posts_df["top_comments"] = posts_df["post_id"].map(top_comments_by_post).apply(lambda lst: lst if isinstance(lst, list) else [])
        posts_df["top_comments"] = posts_df["top_comments"].fillna("").astype(str).tolist()
        
        posts = [
            Post(**{**row, "top_comments": row["top_comments"]})
            for row in posts_df.to_dict(orient="records")
        ]
        
        return posts, comments # Return original comments DataFrame

    def _run(self):
        """
        Runs the Reddit scraper to collect posts and comments.
        """
        logger.info("Starting Reddit scraping...")
        for sub in tqdm(self.subreddits, desc="Subreddits"):
            subreddit = self.reddit.subreddit(sub)
            for post in tqdm(subreddit.top(time_filter="month", limit=self.top_limit), desc=f"Top posts in r/{sub}"):
                self._collect_post_and_comments(post, sub)
            for post in tqdm(subreddit.hot(limit=self.hot_limit), desc=f"Hot posts in r/{sub}"):
                self._collect_post_and_comments(post, sub)
        logger.info("Collected %d posts and %d comments", len(self.posts), len(self.comments))
        self.posts, self.comments = self.add_top_comments(self.posts, self.comments, n=10)

    def get_results(self):
        """
        Returns the collected posts and comments as DataFrames.
        """
        return self.posts, self.comments
