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
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get("type") == "seen":
            self.process_url_seen(adapter)
        elif adapter.get("type") == "crawl":
            self.process_crawl_result(adapter)
        return item
    
    def process_crawl_result(self, adapter):
        self.domains_crawled[adapter.get("domain")] = self.domains_crawled.get(adapter.get("domain"), 0) + 1
        self.total_crawled += 1
        if adapter.get("text") is not None and adapter.get("url") is not None:
            title_text = adapter.get("title") or ''
            body_text = adapter.get("body") or ''
            self.index_writer.add_document(tantivy.Document(
                title=[title_text],
                body=[body_text],
                url=adapter.get("url"),
                text=adapter.get("text"),
                retrieval_date=[adapter.get("date")]))
            self.domains_indexed[adapter.get("domain")] = self.domains_indexed.get(adapter.get("domain"), 0) + 1
            self.total_indexed += 1

    def process_url_seen(self, adapter):
        return
        
    def open_spider(self, spider):
        self.index = qihan_index.getIndex()
        self.index_writer = self.index.writer()

    def close_spider(self, spider):
        self.index_writer.commit()
        self.index_writer.wait_merging_threads()
        with open("stats.txt", 'a') as stats_file:
            stats_file.write("total_crawled: " + str(self.total_crawled))
