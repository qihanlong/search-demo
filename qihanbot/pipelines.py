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
        self.index_writer.add_document(tantivy.Document(
            title=[adapter.get('title')],
            body=[adapter.get('body')],
            url=adapter.get('url'),
            retrieval_date=[adapter.get('date')]))
        return item
        
    def open_spider(self, spider):
        self.debug_file = open('debug.txt', 'w')
        self.index = qihan_index.getIndex()
        self.index_writer = self.index.writer()

    def close_spider(self, spider):
        self.debug_file.close()
        self.index_writer.commit()
        self.index_writer.wait_merging_threads()
