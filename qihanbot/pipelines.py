# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import logging
import tantivy

import qihan_index

class QihanbotPipeline:
    total_crawled = 0
    domains_crawled = {}
    total_indexed = 0
    domains_indexed = {}
    urls_seen = 0
    domains_seen = {}
    url_error = 0
    
    # Routes the outputs from the spider to its appropriate
    # handler. Besides the crawled results, the rest of the
    # outputs are just logging statistics.
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get("type") == "seen":
            self.process_url_seen(adapter)
        elif adapter.get("type") == "crawl":
            self.process_crawl_result(adapter)
        elif adapter.get("type") == "url_error":
            self.process_url_error(adapter)
        return item
        
    def should_index(self, adapter):
        return adapter.get("text") is not None and adapter.get("url") is not None
    
    # Actual crawled urls are handled by this function.
    # Writes the crawled data into the index.
    # Every 10,000 indexed outputs, the index and logged stats
    # are written to disc.
    def process_crawl_result(self, adapter):
        self.domains_crawled[adapter.get("domain")] = self.domains_crawled.get(adapter.get("domain"), 0) + 1
        self.total_crawled += 1
        if self.should_index(adapter):
            title_text = adapter.get("title") or ''
            self.index_writer.add_document(tantivy.Document(
                title=[title_text],
                url=adapter.get("url"),
                headers=adapter.get("headers"),
                text=adapter.get("text"),
                misc=adapter.get("misc"),
                retrieval_date=[adapter.get("date")]))
            self.domains_indexed[adapter.get("domain")] = self.domains_indexed.get(adapter.get("domain"), 0) + 1
            self.total_indexed += 1
            if self.total_indexed % 10000 == 0:
                self.save()

    def process_url_seen(self, adapter):
        self.urls_seen += 1
        self.domains_seen[adapter.get("domain")] = self.domains_seen.get(adapter.get("domain"), 0) + 1
        return

    def process_url_error(self, adapter):
        self.url_error += 1
        return
        
    def open_spider(self, spider):
        self.index = qihan_index.getIndex()
        self.index_writer = self.index.writer()
        
    def save(self):
        self.index_writer.commit()
        with open("stats.txt", 'w') as stats_file:
            stats_file.write("total_crawled: " + str(self.total_crawled))
            stats_file.write("\ntotal_indexed: " + str(self.total_indexed))
            stats_file.write("\nurls_seen: " + str(self.urls_seen))
            stats_file.write("\nurl_error: " + str(self.url_error))
            for domain in self.domains_crawled:
                stats_file.write("\ndomain_crawled:" + domain + " " + str(self.domains_crawled[domain]))
            for domain in self.domains_indexed:
                stats_file.write("\ndomain_indexed:" + domain + " " + str(self.domains_indexed[domain]))
            for domain in self.domains_seen:
                stats_file.write("\ndomain_seen:" + domain + " " + str(self.domains_seen[domain]))

    def close_spider(self, spider):
        self.save()
        self.index_writer.wait_merging_threads()