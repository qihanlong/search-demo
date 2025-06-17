# search-demo
Simple crawler and search engine experiment for finding code documentation. This is built on [scrapy](https://github.com/scrapy/scrapy) and [tantivy-py](https://github.com/quickwit-oss/tantivy-py).

## Installation and Requirements

This repository needs python and pip installed to work. This was developed in python 3.11, but any python3 version should work. Clone the repository locally and finish the setup with the following command.

```
pip install -r requirements
```

## Running

In the directory of the local installation, the crawler can be started with:

```
scrapy crawl qihanbot
```

This defaults to the `fullcrawl.config` settings, but I've also provided `smallcrawl.config` and `minicrawl.config` settings for testing the crawler with a smaller scale crawl. These can be ran with

```
scrapy crawl qihanbot -a config=minicrawl.config
```

After the crawl is initiated, the UI can be started with the following command. A local url will appear in the shell (usually http://127.0.0.1:7860). The UI can be used at the same time as the crawler, but it may take a while for the first content to be available in the index.

```
python3 ui.py
```

## [Technical Details](technical_details.md)

## [Discussion](discussion.md)