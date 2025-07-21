import os
import json
import sqlite3
import traceback
from dataclasses import asdict
from src.logger import setup_logger
import pandas as pd

logger = setup_logger()

def save_json(posts = None, comments = None, save_dir="data"):
    os.makedirs(save_dir, exist_ok=True)
    if posts is not None:
        def convert_timestamps(obj):
            d = asdict(obj)
            for k, v in d.items():
                if isinstance(v, pd.Timestamp):
                    d[k] = v.isoformat()
            return d
        with open(f"{save_dir}/reddit_posts.json", "w", encoding="utf-8") as f:
            json.dump([convert_timestamps(p) for p in posts], f, indent=2, ensure_ascii=False)
    if comments is not None:
        with open(f"{save_dir}/reddit_comments.json", "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in comments], f, indent=2, ensure_ascii=False)

def save_csv(posts = None, comments = None, save_dir="data"):
    os.makedirs(save_dir, exist_ok=True)
    if posts is not None:
        pd.DataFrame([asdict(p) for p in posts]).to_csv(f"{save_dir}/reddit_posts.csv", index=False)
    if comments is not None:
        pd.DataFrame([asdict(c) for c in comments]).to_csv(f"{save_dir}/reddit_comments.csv", index=False)

def save_sqlite(posts = None, comments = None, db_path="data/reddit_data.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        cur = conn.cursor()
        if posts is not None:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT PRIMARY KEY,
                    subreddit TEXT,
                    author TEXT,
                    title TEXT,
                    selftext TEXT,
                    score INTEGER,
                    num_comments INTEGER,
                    created_utc TEXT,
                    flair TEXT,
                    url TEXT,
                    collection_date TEXT,
                    tags TEXT
                )
            """)
            post_tuples = [
                (
                    p.post_id,
                    p.subreddit,
                    p.author,
                    p.title,
                    p.selftext,
                    p.score,
                    p.num_comments,
                    str(p.created_utc) if isinstance(p.created_utc, pd.Timestamp) else p.created_utc,
                    p.flair,
                    p.url,
                    str(p.collection_date) if isinstance(p.collection_date, pd.Timestamp) else p.collection_date,
                    json.dumps(p.tags)
                )
                for p in posts
            ]    
            cur.executemany("INSERT OR IGNORE INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", post_tuples)

        if comments is not None:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    post_id TEXT,
                    subreddit TEXT,
                    author TEXT,
                    body TEXT,
                    score INTEGER,
                    created_utc TEXT,
                    parent_id TEXT,
                    collection_date TEXT,
                    FOREIGN KEY(post_id) REFERENCES posts(post_id)
                )
            """)

            comment_tuples = [tuple(asdict(c).values()) for c in comments]
            cur.executemany("INSERT OR IGNORE INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", comment_tuples)

        conn.commit()
    except Exception as e:
        logger.error("Error saving data to SQLite...\n %s", traceback.print_exc)
        raise e
    finally:
        conn.close()