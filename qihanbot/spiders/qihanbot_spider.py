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
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "USER_AGENT": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20 qihanbot https://github.com/qihanlong/search-demo",
        "ROBOTSTXT_USER_AGENT": "qihanbot",
    }
    priority_keywords = {"doc":2, "api":2, "ref":2, "forum":-2, "community":-2, "bug":-1, "user":-1, "issue":-1, "blog":-1}

    def __init__(self, config=None, *args, **kwargs):
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
        if content_type.startswith(b"text/html"):
            yield {"type": "crawl",
                "url": response.url,
                "body": response.xpath("//body").get(),
                "title": response.xpath("//title/text()").get(),
                "headers": response.xpath("//h1/text()").getall() + response.xpath("//h2/text()").getall() + response.xpath("//h3/text()").getall() + response.xpath("//h4/text()").getall(),
                "text": response.xpath("//p/text()").getall(),
                "misc": response.xpath("//div/text()").getall() + response.xpath("//span/text()").getall(),
                "date": datetime.today(),
                "domain": crawl_util.matchDomain(self.allowed_domains, response.url)}
            next_urls = response.xpath("//a/@href").getall()
            for next_url in next_urls:
                if next_url.startswith("mailto:"):
                    yield {"type": "mail", "url": next_url}
                    continue
                if next_url.startswith("tel:"):
                    yield {"type": "phone", "url": next_url}
                    continue
                next_request = response.follow(next_url)
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
                yield {"type": "seen", "url": next_request.url, "domain": crawl_util.matchDomain(self.allowed_domains, next_request.url)}
                yield next_request








