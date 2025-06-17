# Technical Details

## [Scrapy](https://github.com/scrapy/scrapy)

The crawler uses Scrapy as its engine. The crawler sends the following user agent and obeys rules for `qihanbot`. The crawl is capped at 2 concurrent connections per domain with back-offs based on the domain's response latency. All these settings can be updated in the `qihanbot/settings.py` file (see https://docs.scrapy.org/en/latest/topics/settings.html for details).

```
Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20 qihanbot (+https://github.com/qihanlong/search-demo)
```

### Crawl Configuration

Settings not handled by Scrapy (such as domains and crawl limits) are set by the `.config` files. These include a list of starting urls, a list of additional domains, and the number of urls to crawl per domain. The full crawl domain limits include both the starting url's domains and the additional domains. Examples of these configuration files include:

- `fullcrawl.config`: Includes the full list of starting urls and

### URL Selection

"doc":2, "api":2, "ref":2, "wiki":1, "forum":-2, "community":-2, "bug":-1, "user":-1, "issue":-1, "blog":-1, "release": -1, "download":-1

## [Tantivy](https://tantivy-py.readthedocs.io/en/latest/)

The Title, headers, and text in <p>, <div>, and <span> tags are exported to Tantivy for indexing.

Only indexed if there is relevant text in <p> tags

Searching
- latency includes both the search time and the time it took to parse the results for display. The overall latency was low enough that I didn't see the need to split hairs.
- index is reloaded every time someone visits the UI.