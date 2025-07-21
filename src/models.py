from dataclasses import field, dataclass
from typing import List, Optional

@dataclass
class Post:
    post_id: str
    subreddit: str
    author: str
    title: str
    selftext: str
    score: int
    num_comments: int
    created_utc: str
    flair: Optional[str]
    url: str
    collection_date: str
    tags: List[str] = field(default_factory=list)
    top_comments: str = ""
    cluster_labels: Optional[List[int]] = field(default_factory=list)

@dataclass
class Comment:
    comment_id: str
    post_id: str
    subreddit: str
    author: str
    body: str
    score: int
    created_utc: str
    parent_id: str
    collection_date: str