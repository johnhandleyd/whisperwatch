import pandas as pd
import os
import numpy as np

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

# Load existing data
tagged_posts = pd.read_csv(config.DATA_SAVE_DIR + "/reddit_posts.csv")
tagged_posts['created_utc'] = pd.to_datetime(tagged_posts['created_utc'])
comments = pd.read_csv(config.DATA_SAVE_DIR + "/reddit_comments.csv")

report_generator = ReportGenerator(
    posts=tagged_posts,
    template_dir=config.TEMPLATE_DIR,
    output_dir=config.REPORTS_SAVE_DIR
)
report_generator.run()