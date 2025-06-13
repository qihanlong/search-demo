from datetime import datetime
import logging
import scrapy
from scrapy.utils.request import fingerprint
from scrapy.exceptions import CloseSpider
from urllib.parse import urlparse


class QihanBot(scrapy.Spider):
    name = "qihanbot"
    start_urls = [
        "http://angular.io/",
        "http://api.drupal.org/",
        "http://swift.org/",
        "http://nginx.org/"
    ]
    allowed_domains = {}
    # allowed_domains = {"swift.org"}
    max_downloads = 100
    max_downloads_per_domain = 10
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 0.1,
        "USER_AGENT": "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20 qihanbot",
        "ROBOTSTXT_USER_AGENT": "qihanbot",
        # "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",
        # "DUPEFILTER_DEBUG": True
    }
    priority_keywords = ["doc", "api"]

    def __init__(self, config=None, *args, **kwargs):
        super(QihanBot, self).__init__(*args, **kwargs)
        logging.info("qihanbot __init__")
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

    def matchDomain(self, url):
        domain = urlparse(url).netloc
        # Majority of the time, the domain should be an exact match
        if domain in self.allowed_domains:
            return domain
        # Check for subdomain matches starting with the longest.
        split_domain = domain.split('.')
        for i in range(1, len(split_domain)):
            d = '.'.join(split_domain[i:])
            if d in self.allowed_domains:
                return d
        if len(split_domain) >= 2:
            # If it's not found, just return the second level domain.
            return '.'.join(split_domain[-2:])
        return ''

    def updateAllowedDomains(self):
        logging.info("updateAllowedDomains called")
        if not isinstance(self.allowed_domains, list):
            self.allowed_domains = set(self.allowed_domains)
        if not isinstance(self.allowed_domains, set):
            self.allowed_domains = set()
        for url in self.start_urls:
            domain_key = self.matchDomain(url)
            if len(domain_key) > 0:
                self.allowed_domains.add(domain_key)

    def parse(self, response):
        content_type = response.headers.get("Content-Type")
        if content_type.startswith(b"text/html"):
            yield {"url": response.url,
                "body": response.xpath("//body").get(),
                "title": response.xpath("//title").get(),
                "date": datetime.today()}
            next_urls = response.xpath("//a/@href").getall()
            for next_url in next_urls:
                if next_url.startswith("mailto:"):
                   continue
                next_request = response.follow(next_url)
                if not next_request.url.startswith("http"):
                    continue
                parsed_url = urlparse(next_request.url)
                # We're looking for documentation, so prioritize documentation related keywords
                for keyword in self.priority_keywords:
                    if keyword in parsed_url.path:
                        next_request.priority += 1
                    if keyword in parsed_url.netloc:
                        next_request.priority += 1
                yield next_request








