# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from gb_parse.items import GbHhruEmployerItem


class GbInstagramPipeline:
    def process_item(self, item, spider):
        client = MongoClient()
        collection = item.__class__.__name__.replace('Item', '')
        self.db = client["gb_parse_16_02_2021"]
        # if collection == "GbInstaUser" and self.db[collection].find_one({"user_id": item.get("user_id")}):
        #     return None
        self.db[collection].insert_one(item)
        return item


class GbParsePipeline:
    def process_item(self, item, spider):
        client = MongoClient()
        self.db = client["gb_parse_16_02_2021"]
        if item.get("collection_name", False):
            collection = f"{spider.name}_{item['collection_name']}"
            self.db[collection].insert_one(item["data"])
        else:
            self.db[spider.name].insert_one(item)

        return item

# class GbImageDownloadPipeline(ImagesPipeline):
#     def get_media_requests(self, item, info):
#         if item["data"].get("display_url"):
#             yield Request(item["data"]["display_url"])
#
#     def item_completed(self, results, item, info):
#         if item["data"].get("display_url"):
#             item["data"]["display_url"] = results[0][1]
#         return item


# class GbImageDownloadPipeline(ImagesPipeline):
#     def get_media_requests(self, item, info):
#         for url in item.get("photos", []):
#             yield Request(url)
#
#     def item_completed(self, results, item, info):
#         if item.get("photos"):
#             item["photos"] = [itm[1] for itm in results]
#         return item

# class GbParseMongoPipeline:
#     def __init__(self):
#         client = MongoClient()
#         self.db = client["gb_parse_16_02_2021"]
#
#     def process_item(self, item, spider):
#         self.db[spider.name].insert_one(item)
#         return item
