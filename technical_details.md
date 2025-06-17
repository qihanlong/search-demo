# Technical Details

## [Scrapy](https://github.com/scrapy/scrapy)

The crawler uses Scrapy as its engine with the goal of being a well behaved crawler for a search engine. Redirects, throttling, http errors, and dupe filtering are all handled by Scrapy.

The crawler sends the following user agent and obeys rules for `qihanbot`. The crawl is capped at 2 concurrent connections per domain with back-offs based on the domain's response latency. All these settings can be updated in the `qihanbot/settings.py` file (see https://docs.scrapy.org/en/latest/topics/settings.html for details).

```
Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20 qihanbot (+https://github.com/qihanlong/search-demo)
```

### Crawl Configuration

Settings not handled by Scrapy (such as domains and crawl limits) are set by the `.config` files to allow for easy swapping for testing. These include a list of starting urls, a list of additional domains, and the number of urls to crawl per domain. The full crawl domain limits include both the starting url's domains and the additional domains. Examples of these configuration files include:

- `fullcrawl.config`: Includes the full list of starting urls, no global crawl cap, and 10000 download cap per domain. This is the default setting.
- `smallcrawl.config`: Uses a 20 domain subset of `fullcrawl.config` as the starting urls with a 10000 global crawl cap and 500 crawls per domain cap.
- `minicrawl.config`: Contains 4 starting urls that doesn't overlap with `smallcrawl.config` with a 200 global crawl cap and 50 crawls per domain cap. This usually takes around 2 minutes to complete on my machine.

The configurations can be set with `-a config=` at the end of the scrapy command. i.e.

```
scrapy crawl qihanbot -a config=minicrawl.config
```

### URL Selection

The bot crawls attempts to crawl all valid http urls that it finds until the download cap is reached. Any non-http urls and urls that ends in `.pdf`, `.zip`, and `.gz` are dropped before queuing. In order to help direct the crawler to relevant content, it uses a small list of substrings to match against the url before being placed into the priority queue for schedling. Finally, urls ending in `.html` are also boosted.

- `doc`:2
- `api`:2
- `ref`:2
- `wiki`:1
- `forum`:-2
- `community`:-2
- `bug`:-1
- `user`:-1
- `issue`:-1
- `blog`:-1
- `release`: -1
- `download`:-1

Once the url is crawled, we drop all results that don't have the `text/html` content type before sending the contents to parsing.

## [Tantivy](https://tantivy-py.readthedocs.io/en/latest/)

Indexing and searching is done through the Tantivy-py library. The index schema includes fields for the url, retrieval date, title, headers, and text in `<p>`, `<div>`, and `<span>` tags. Results are only indexed if there is relevant text in `<p>` tags. The index and search statistics are written every 10,000 documents. This allows the UI to be run at the same time as the crawler.

Searching is done through a gradio ui and the index is reloaded every time someone refreshes the page. The query is directly sent to Tantivy and supports tantivy's query language (See [Valid Query Formats](https://tantivy-py.readthedocs.io/en/latest/reference/)). Certain fields are boosted more to improve search relevancy.

- `title`:3
- `headers`:2
- `<p>`:1
- `url`:1
- `<div>` and `<span>`:0.5

The UI also includes some statistics. The search latency displayed with every search includes both the search time and the time it took to parse the results for display. The overall latency was low enough that I didn't see the need to split hairs.

Crawl statistics are displayed below the search box in a collapsed accordion. This includes both overall statistics and top domain statistics. The individual domains can be filtered with the textbox.

















