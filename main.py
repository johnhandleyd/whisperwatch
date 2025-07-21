import pandas as pd

from src.reddit_scraper import RedditScraper
from src import config
from src.storage import save_json, save_csv, save_sqlite
from src.tagger import tag_post
from src.logger import setup_logger
from src.clustering import Clustering
from src.generate_report import ReportGenerator
from src.utils import ensure_all_dirs

logger = setup_logger()

# Ensure necessary directories exist
ensure_all_dirs()

def main(run_scraper: bool = False, run_clustering: bool = False, run_report: bool = True, embeddings_file: str = "reddit_posts_mpnet.npy"):
    logger.info("Starting WhisperWatch collection pipeline...")
    logger.debug("Running with config: %s", config.SUBREDDITS)
    if run_scraper:
        logger.info("Running Reddit scraper...")
        scraper = RedditScraper(
            subreddits=config.SUBREDDITS,
            top_limit=config.TOP_POSTS,
            hot_limit=config.HOT_POSTS,
            min_comments=config.MIN_COMMENTS,
            min_score=config.MIN_SCORE,
            max_comments_per_post=config.MAX_COMMENTS_PER_POST
        )

        scraper._run()
        posts, comments = scraper.get_results()
        
        logger.info("Tagging posts...")
        tagged_posts = [tag_post(post) for post in posts]

        logger.info("Collected %d posts and %d comments. Saving...", len(tagged_posts), len(comments))

        save_json(tagged_posts, comments, config.DATA_SAVE_DIR)
        save_csv(tagged_posts, comments, config.DATA_SAVE_DIR)
        save_sqlite(tagged_posts, comments, config.DB_PATH)

        logger.info("All data saved. WhisperWatch collection complete.")
    else:
        logger.info("Skipping Reddit scraper, using existing data...")

        # Load existing data
        tagged_posts = pd.read_csv(config.DATA_SAVE_DIR + "/reddit_posts.csv")
        tagged_posts['created_utc'] = pd.to_datetime(tagged_posts['created_utc'])
        comments = pd.read_csv(config.DATA_SAVE_DIR + "/reddit_comments.csv")

    if run_clustering:
        logger.info("Running clustering...")
        clustering = Clustering(posts=tagged_posts, comments=comments, embeddings_file=embeddings_file)
        clustering._run()

    # Run analysis report generation
    if run_report:
        logger.info("Generating analysis report...")
        report_generator = ReportGenerator(posts=tagged_posts, template_dir=config.TEMPLATE_DIR, output_dir=config.REPORTS_SAVE_DIR)
        report_generator.run()

if __name__ == "__main__":
    main(run_scraper=False, run_clustering=True, run_report=True, embeddings_file="reddit_embeddings_mpnet_v1.npy")
