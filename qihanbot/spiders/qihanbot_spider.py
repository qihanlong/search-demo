from datetime import datetime
import logging
import scrapy
from scrapy.utils.request import fingerprint
from scrapy.exceptions import CloseSpider
from urllib.parse import urlparse

import crawl_util

class QihanBot(scrapy.Spider):
    name = "qihanbot"
    start_urls = [
    ]
    allowed_domains = {}
    max_downloads = 100
    max_downloads_per_domain = 10

    # Keywords in the url that's used to direct the priority queue for crawling.
    priority_keywords = {"doc":2, "api":2, "ref":2, "wiki":1, "forum":-2, "community":-2, "bug":-1, "user":-1, "issue":-1, "blog":-1, "release": -1, "download":-1}

    def __init__(self, config="fullcrawl.config", *args, **kwargs):
        super(QihanBot, self).__init__(*args, **kwargs)
        if config:
            logging.info("opening " + config)
            with open(config, 'r') as file:
                mode = None
                for line in file:
                    line = line.strip(" \n")
                    logging.info(line)
                    if line == "start_urls:":
                        mode = "start_urls"
                        self.start_urls = []
                        continue
                    if line == "additional_allowed_domains:":
                        mode = "additional_allowed_domains"
                        self.allowed_domains = set()
                        continue
                    if line.startswith("max_downloads:"):
                        val = line.removeprefix("max_downloads:")
                        self.max_downloads = int(val)
                        mode = None
                        continue
                    if line.startswith("max_downloads_per_domain:"):
                        val = line.removeprefix("max_downloads_per_domain:")
                        self.max_downloads_per_domain = int(val)
                        mode = None
                        continue
                    if mode == "start_urls" and len(line) > 0:
                        self.start_urls.append(line)
                    elif mode == "additional_allowed_domains" and len(line) > 0:
                        self.allowed_domains.add(line)
        self.updateAllowedDomains()

    # Adds the domains of the starting urls to the list of allowed domains.
    def updateAllowedDomains(self):
        logging.info("updateAllowedDomains called")
        if not isinstance(self.allowed_domains, list):
            self.allowed_domains = set(self.allowed_domains)
        if not isinstance(self.allowed_domains, set):
            self.allowed_domains = set()
        for url in self.start_urls:
            domain_key = crawl_util.matchDomain(self.allowed_domains, url)
            if len(domain_key) > 0:
                self.allowed_domains.add(domain_key)

    def parse(self, response):
        content_type = response.headers.get("Content-Type")
        if content_type and content_type.startswith(b"text/html"):
            yield {"type": "crawl",
                "url": response.url,
                "title": response.xpath("//title/text()").get(),
                "headers": [p for p in (response.xpath("//h1/text()").getall() + response.xpath("//h2/text()").getall() + response.xpath("//h3/text()").getall() + response.xpath("//h4/text()").getall()) if len(p) > 2],
                "text": [p for p in response.xpath("//p/text()").getall() if len(p) > 4],
                "misc": [p for p in (response.xpath("//div/text()").getall() + response.xpath("//span/text()").getall()) if len(p) > 4],
                "date": datetime.today(),
                "domain": crawl_util.matchDomain(self.allowed_domains, response.url)}
            
            # Add all links in the response to the scheduler.
            next_urls = response.xpath("//a/@href").getall()
            for next_url in next_urls:
                try:
                    next_request = response.follow(next_url)
                except ValueError:
                    yield {"type": "url_error", "url": next_url}
                    continue
                if not next_request.url.startswith("http"):
                    yield {"type": "nonhttp", "url": next_request.url}
                    continue
                parsed_url = urlparse(next_request.url)
                # We're looking for documentation, so prioritize documentation related keywords
                for keyword in self.priority_keywords:
                    if keyword in parsed_url.path:
                        next_request.priority += self.priority_keywords[keyword]
                    if keyword in parsed_url.netloc:
                        next_request.priority += self.priority_keywords[keyword]
                # Prioritize html extensions
                if next_request.url.endswith(".html") or next_request.url.endswith(".htm"):
                    next_request.priority += 2
                yield {"type": "seen", "url": next_request.url, "domain": crawl_util.matchDomain(self.allowed_domains, next_request.url)}
                # Some common file types that we can't index, so we shouldn't bother
                # scheduling them.
                if next_request.url.endswith(".pdf") or next_request.url.endswith(".zip") or next_request.url.endswith(".gz"):
                    continue
                yield next_request








