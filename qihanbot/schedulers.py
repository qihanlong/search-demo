import logging
from scrapy.core.scheduler import Scheduler
from urllib.parse import urlparse

# A scheduler class that implements a max crawl count and max crawl per domain enforcement.
class QihanScheduler(Scheduler):
    def __init__(
        self, dupefilter, jobdir, dqclass, mqclass, logunser, stats, pqclass, crawler
    ):
        super().__init__(dupefilter, jobdir, dqclass, mqclass, logunser, stats, pqclass, crawler)
        self.max_downloads = 100
        self.max_downloads_per_domain = 10
        self.domains = set()
        self.count = 0
        self.count_per_domain = {}
        
    # TODO: move to util file?
    def matchDomain(self, url):
        domain = urlparse(url).netloc
        # Majority of the time, the domain should be an exact match
        if domain in self.domains:
            return domain
        # Check for subdomain matches starting with the longest.
        split_domain = domain.split('.')
        for i in range(1, len(split_domain)):
            d = '.'.join(split_domain[i:])
            if d in self.domains:
                return d
        if len(split_domain) >= 2:
            # If it's not found, just return the second level domain.
            return '.'.join(split_domain[-2:])
        return ''
        
    def open(self, spider):
        if spider.allowed_domains:
            self.domains.update(spider.allowed_domains)
        if hasattr(spider, 'max_downloads'):
            self.max_downloads = spider.max_downloads
        if hasattr(spider, 'max_downloads_per_domain'):
            self.max_downloads_per_domain = spider.max_downloads_per_domain
        return super().open(spider)
        
    
    def enqueue_request(self, request) -> bool:
        if self.max_downloads >= 0 and self.count >= self.max_downloads:
            logging.info("Max downloads reached. Dropping request to <" + request.url + ">")
            return False
        domain_key = self.matchDomain(request.url)
        if self.max_downloads_per_domain >= 0 and self.count_per_domain.get(domain_key, 0) >= self.max_downloads_per_domain:
            logging.info("Max downloads reached for domain <" + domain_key + ">. Dropping request to <" + request.url + ">")
            return False
        enqueued = super().enqueue_request(request)
        if enqueued:
            self.count += 1
            self.count_per_domain[domain_key] = self.count_per_domain.get(domain_key, 0) + 1
        return enqueued