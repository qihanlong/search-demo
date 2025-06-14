# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import logging
import qihan_index
import tantivy

class QihanbotPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get("text") is not None and adapter.get("url") is not None:
            title_text = adapter.get("title") or ''
            body_text = adapter.get("body") or ''
            self.index_writer.add_document(tantivy.Document(
                title=[title_text],
                body=[body_text],
                url=adapter.get("url"),
                text=adapter.get("text"),
                retrieval_date=[adapter.get("date")]))
        return item
        
    def open_spider(self, spider):
        self.debug_file = open("debug.txt", 'w')
        self.index = qihan_index.getIndex()
        self.index_writer = self.index.writer()

    def close_spider(self, spider):
        self.debug_file.close()
        self.index_writer.commit()
        self.index_writer.wait_merging_threads()
