import scrapy
from urllib.parse import unquote
import json
import base64

from gb_parse.loaders import AutoyoulaLoader


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    _nav_xpath = {
        "brands": "//div[contains(@class, 'ColumnItemList_container')]//"
                  "div[contains(@class, 'ColumnItemList_item')]//a[@class='blackLink']/@href",
        "car": "//div[@id='serp']//a[contains(@class, 'SerpSnippet_name')]/@href",
        "pagination": "//div[contains(@class, 'Paginator_block')]//a[contains(@class, 'Paginator_button')]/@href"
    }

    _car_xpaths = {
        "title": "//div[@data-target='advert']//div[@data-target='advert-title']/text()",
        "price": "//div[contains(@class, 'app_gridContainer')]//"
                 "div[contains(@class, 'AdvertCard_price')]/text()",
        "photos": "//div[@data-target='advert']//"
                  "figure[contains(@class, 'PhotoGallery_photo')]//img/@src",
        "description": "//div[contains(@class, 'app_gridContainer')]//"
                       "div[contains(@class, 'AdvertCard_descriptionInner')]/text()",
        "characteristics": "//div[@data-target='advert']//"
                           "h3[contains(text(), 'Характеристики')]/../div/div",
        "author": "//script[contains(text(), 'window.transitState')]/text()",
        "phone": "//script[contains(text(), 'window.transitState')]/text()"
    }

    def _get_follow(self, response, select_str, callback, **kwargs):
        for link in response.xpath(select_str):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):
        yield from self._get_follow(response, self._nav_xpath["brands"], self.brand_parse)

    def brand_parse(self, response, *args, **kwargs):
        yield from self._get_follow(response, self._nav_xpath["car"], self.car_parse)
        yield from self._get_follow(response, self._nav_xpath["pagination"], self.brand_parse)

    def car_parse(self, response, *args, **kwargs):
        loader = AutoyoulaLoader(response=response)
        loader.add_value("url", response.url)
        for key, selector in self._car_xpaths.items():
            loader.add_xpath(key, selector)

        yield loader.load_item()
