**WhisperWatch: Reddit Narrative Clustering & Suspicious Activity Detection**

**Table of Contents**

* [Project Overview](#project-overview)
* [Features](#features)
* [Architecture & Pipeline](#architecture--pipeline)
* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Module Descriptions](#module-descriptions)
* [Suspicious Behavior Detectors](#suspicious-behavior-detectors)
* [Report Generation](#report-generation)
* [Contributing](#contributing)
* [License](#license)

---

## Project Overview

WhisperWatch is an OSINT-focused toolkit for scraping, analyzing, and reporting on narratives emerging across Reddit. It collects posts and comments from target subreddits, processes them into embeddings, clusters them into coherent narratives, and flags suspicious coordinated behavior—surfacing potential information operations or coordinated campaigns.

This project demonstrates modern NLP (Sentence-BERT), clustering (HDBSCAN), and anomaly-detection techniques, topped off with automated HTML reporting for seamless review.

## Features

* **Reddit Data Collection**: Scrape posts and top comments from configurable subreddits.
* **Text Cleaning & Enrichment**: Remove junk, join titles/selftexts, and attach top-N informative comments.
* **Embedding & Dimensionality Reduction**: Generate embeddings (`all-mpnet-base-v2`), reduce with PCA.
* **Clustering**: Leverage HDBSCAN with grid search to identify narrative clusters.
* **Suspicious Activity Detection**: Multi-layer detectors for burst posting, near-duplicates, account metadata heuristics (to be expanded).
* **Automated Reporting**: Generate timestamped HTML reports with cluster summaries, visualizations, and flags.

## Architecture & Pipeline

```text
+----------------+       +-------------+       +-----------------+       +---------------+       +--------------+  
| RedditScraper  | --->  | DataStorage | --->  | TextPreprocessor | --->  | Embedding     | --->  | Clustering   |  
+----------------+       +-------------+       +-----------------+       +---------------+       +--------------+  
                                                                                                  |            
                                                                                                  v            
                                                                                           +---------------+  
                                                                                           | ReportGenerator|  
                                                                                           +---------------+  
```

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-org/whisperwatch.git  
   cd whisperwatch  
   ```
2. **Create a virtual environment & install dependencies**

   ```bash
   python3 -m venv venv  
   source venv/bin/activate  
   pip install -r requirements.txt  
   ```
3. **Set up PostgreSQL (optional)**

   * Create database and user; update `config.py` accordingly.

## Configuration

All settings are in `config.py` as variables:

```python
SUBREDDITS = ["politics", "conspiracy", "worldnews", "Conservative"]
TOP_POSTS = 50
HOT_POSTS = 50
MIN_SCORE = 10
MIN_COMMENTS = 10
MAX_COMMENTS_PER_POST = 50

DATA_SAVE_DIR = "data"
REPORTS_SAVE_DIR = "reports"
TEMPLATE_DIR = "templates"

DB_PATH = "data/reddit_data.db"
```

## Usage

Run the full pipeline end-to-end:

```bash
python main.py
```

To run without scraping or clustering, or to supply existing embeddings, or to only run the report generator, edit the arguments inside ```main()``` in main.py:
```python
main(run_scraper=False/True, run_clustering=False/True, run_report=False/True, embeddings_file=path_to_npy_file.npy)
```

This will be improved with CLI commands soon.

## Module Descriptions

* **scraper.py**: `RedditScraper` class for Pushshift/Reddit API calls, saving to CSV/SQL/JSON.
* **storage.py**: Centralized I/O for CSV, SQL, JSON.
* **preprocessor.py**: Text cleaning, title/selftext join, comment enrichment.
* **embedder.py**: Embedding generation (SentenceTransformer) + PCA.
* **clusterer.py**: HDBSCAN clustering with grid search.
* **suspicious.py**: Anomaly detectors (burst, duplicate, metadata, graph, domain, linguistics). # To be improved
* **report.py**: `ReportGenerator` for HTML output with plots showing clusters found.

## Report Generation

Reports are auto-saved under `reports/yyyy-mm-dd_HHMMSS/`. Each report includes:

* Cluster overview with keywords & examples
* Time-series plots of posting activity
* Top authors & their metadata
* Highlighted suspicious clusters & users

To customize the HTML template, modify `templates/report.html` and re-run `python main.py`.

## Contributing

Contributions welcome! Please open issues or submit pull requests for new detectors, optimization, or bug fixes.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
