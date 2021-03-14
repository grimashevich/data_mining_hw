# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from itemadapter import ItemAdapter
from pymongo import MongoClient

from gb_parse.items import GbHhruEmployerItem


class GbParsePipeline:
    def process_item(self, item, spider):
        client = MongoClient()
        self.db = client["gb_parse_16_02_2021"]
        if isinstance(item, GbHhruEmployerItem):
            collection = spider.name + '_employers'
        else:
            collection = spider.name
        self.db[collection].insert_one(item)
        return item


# class GbParseMongoPipeline:
#     def __init__(self):
#         client = MongoClient()
#         self.db = client["gb_parse_16_02_2021"]
#
#     def process_item(self, item, spider):
#         self.db[spider.name].insert_one(item)
#         return item