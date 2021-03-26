# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class GbAutoYoulaItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    price = scrapy.Field()
    photos = scrapy.Field()
    characteristics = scrapy.Field()
    description = scrapy.Field()
    author = scrapy.Field()
    phone = scrapy.Field()


class GbHhruVacancyItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    skills = scrapy.Field()
    employer_url = scrapy.Field()


class GbHhruEmployerItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    site_url = scrapy.Field()
    service = scrapy.Field()
    description = scrapy.Field()


class GbInstaUserItem(scrapy.Item):
    _id = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    followers = scrapy.Field()
    followed = scrapy.Field()
    handshakes = scrapy.Field()     # Пользователи со взаимной подпиской. Сохраняем в БД только их
    step = scrapy.Field()            # Кол-во шагов от первого, до искомого пользователя


class GbInstaFollowerItem(scrapy.Item):
    _id = scrapy.Field()
    insta_user_id = scrapy.Field()
    follower_id = scrapy.Field()

