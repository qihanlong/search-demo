import logging
from scrapy.core.scheduler import Scheduler

import crawl_util

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
        
    def open(self, spider):
        if spider.allowed_domains:
            self.domains.update(spider.allowed_domains)
        if hasattr(spider, "max_downloads"):
            self.max_downloads = spider.max_downloads
        if hasattr(spider, "max_downloads_per_domain"):
            self.max_downloads_per_domain = spider.max_downloads_per_domain
        return super().open(spider)
        
    
    def enqueue_request(self, request) -> bool:
        if self.max_downloads >= 0 and self.count >= self.max_downloads:
            self.count += 1
            if self.count < self.max_downloads + 10:
                logging.debug("Max downloads reached. Dropping request to <" + request.url + ">")
            return False
        domain_key = crawl_util.matchDomain(self.domains, request.url)
        if self.max_downloads_per_domain >= 0 and self.count_per_domain.get(domain_key, 0) >= self.max_downloads_per_domain:
            self.count_per_domain[domain_key] += 1
            if self.count_per_domain[domain_key] < self.max_downloads_per_domain + 10:
                logging.debug("Max downloads reached for domain <" + domain_key + ">. Dropping request to <" + request.url + ">")
            return False
        enqueued = super().enqueue_request(request)
        if enqueued:
            self.count += 1
            self.count_per_domain[domain_key] = self.count_per_domain.get(domain_key, 0) + 1
        return enqueued