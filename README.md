# search-demo
Simple crawler and search engine for finding code documentation.

## Installation and Requirements

This was developed in python 3.11, but any python3 version should work. Clone the repository locally and finish the setup with the following command.

```
pip install -r requirements
```

## Running

In the directory of the local installation, the crawler can be started with:

```
scrapy crawl qihanbot
```

This defaults to the `fullcrawl.config` settings, but I've also provided `smallcrawl.config` and `minicrawl.config` settings for testing the crawler. These can be ran with

```
scrapy crawl qihanbot -a config=minicrawl.config
```

After the crawl is underway, the UI can be started with the following command. A local url will appear in the shell (usually 127.0.0.1:7860).
```
python3 ui.py
```

## [Overview](overview.md)

## [Technical Details](techinical_details.md)

## TODO
- Improve search rankings
- Write documentation