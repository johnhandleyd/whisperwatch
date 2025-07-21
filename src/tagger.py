from typing import List

def tag_post(post) -> List[str]:
    tags = []

    title = (post.title or "").lower()
    body = (post.selftext or "").lower()
    flair = (post.flair or "").lower()

    conspiracy_keywords = ["deep state", "hoax", "false flag", "great reset", "illuminati"]
    misinfo_keywords = ["5g", "plandemic", "bioweapon", "graphene", "cancer cure", "chemtrails"]

    if any(kw in title or kw in body for kw in misinfo_keywords):
        tags.append("potential_misinfo")
    
    if any(kw in title or kw in body for kw in conspiracy_keywords):
        tags.append("conspiracy")

    if post.subreddit.lower() == "conspiracy":
        tags.append("conspiracy")

    if post.num_comments > 300 or post.score > 1000:
        tags.append("high_engagement")

    if post.num_comments < 5 and post.score < 5:
        tags.append("low_engagement")

    if "[deleted]" in post.author.lower():
        tags.append("deleted_author")

    if "satire" in flair or "joke" in flair:
        tags.append("likely_satire")

    if post.subreddit.lower() == "politics" or any(x in flair for x in ["dem", "gop", "liberal", "conservative"]):
        tags.append("political")

    if len(post.selftext.strip()) > 1000:
        tags.append("theory_drop")

    if post.selftext.strip() == "":
        tags.append("url_only")
        
    post.tags = tags
    return post
