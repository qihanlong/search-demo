from datetime import datetime
import logging
import scrapy
from scrapy.utils.request import fingerprint
from scrapy.exceptions import CloseSpider
from urllib.parse import urlparse


class QihanBot(scrapy.Spider):
    name = 'qihanbot'
    start_urls = [
        'http://angular.io/',
        'http://api.drupal.org/',
        'http://swift.org/',
        'http://nginx.org/'
    ]
    allowed_domains = {'angular.io', 'nginx.org', 'swift.org', 'api.drupal.org'}
    # allowed_domains = {'swift.org'}
    custom_settings = {
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'DOWNLOAD_DELAY': 0.1,
        'USER_AGENT': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20 qihanbot',
        'ROBOTSTXT_USER_AGENT': 'qihanbot',
        # 'DUPEFILTER_CLASS': 'scrapy.dupefilters.RFPDupeFilter',
        # 'DUPEFILTER_DEBUG': True
    }
    priority_keywords = ['doc', 'api']

    def __init__(self):
        super().__init__()
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
        if not isinstance(self.allowed_domains, list):
            self.allowed_domains = set(self.allowed_domains)
        if not isinstance(self.allowed_domains, set):
            self.allowed_domains = set()
        for url in self.start_urls:
            domain_key = self.matchDomain(url)
            if len(domain_key) > 0:
                self.allowed_domains.add(domain_key)

    def parse(self, response):
        content_type = response.headers.get('Content-Type')
        if content_type.startswith(b'text/html'):
            yield {'url': response.url,
                'body': response.xpath('//body').get(),
                'title': response.xpath('//title').get(),
                'date': datetime.today()}
            next_urls = response.xpath('//a/@href').getall()
            for next_url in next_urls:
                next_request = response.follow(next_url)
                if not next_request.url.startswith('http'):
                    continue
                parsed_url = urlparse(next_request.url)
                # We're looking for documentation, so prioritize documentation related keywords
                for keyword in self.priority_keywords:
                    if keyword in parsed_url.path:
                        next_request.priority += 1
                    if keyword in parsed_url.netloc:
                        next_request.priority += 1
                yield next_request








