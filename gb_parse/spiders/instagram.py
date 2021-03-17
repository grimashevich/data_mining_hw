import json
import scrapy
from jsonpath_ng import jsonpath, parse
from datetime import datetime
from random import randint

class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    _login_url = "https://www.instagram.com/accounts/login/ajax/"
    _tags_path = "/explore/tags/"
    _graphql_url = 'https://www.instagram.com/graphql/query/'

    _query_cache = {
        "posts": "9b498c08113f1e09617a1703c22b2f32"
    }

    _json_xpath = {
        "post_node": "$..hashtag.edge_hashtag_to_media.edges[*].node",
        "first_page_node": "$..hashtag.edge_hashtag_to_media|"
                           "edge_hashtag_to_top_posts.edges[*].node",
        "next_page": "$..hashtag.edge_hashtag_to_media.page_info",
        "tag_info": "$..TagPage[0]..hashtag",
    }

    def __init__(self, login, password, tags, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.tags = tags

    def parse(self, response, *args, **kwargs):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self._login_url,
                method="POST",
                callback=self.parse,
                formdata={"username": self.login, "enc_password": self.password},
                headers={"X-CSRFToken": js_data["config"]["csrf_token"]},
            )
        except AttributeError as e:
            if response.json()["authenticated"]:
                print("Авторизация прошла успешно")
                for tag in self.tags:
                    yield response.follow(f"{self._tags_path}{tag}/", callback=self.tag_page_parse,
                                          cb_kwargs={'tag': tag})

    def tag_page_parse(self, response, *args, **kwargs):
        if 'json' in str(response.headers['Content-Type']):
            jsn = json.loads(response.text)
            json_nodes = self._json_xpath["post_node"]
        else:
            jsn = self.js_data_extract(response)
            json_nodes = self._json_xpath["first_page_node"]
            yield {
                "collection_name": "tag_info",
                "data": self.get_tag_info(jsn)
            }

        for itm in self.get_json_xpath(jsn, json_nodes):
            yield {
                "date_parse": datetime.now(),
                "data": itm
            }

        next_page = next(self.get_json_xpath(
            jsn, self._json_xpath["next_page"]))
        if next_page["has_next_page"]:
            next_page_url = f'{self._graphql_url}?query_hash={self._query_cache["posts"]}&' \
                            f'variables={{"tag_name":"{kwargs["tag"]}","first":{randint(3, 12)},' \
                            f'"after":"{next_page["end_cursor"]}"}}'
            yield response.follow(next_page_url,
                                  callback=self.tag_page_parse,
                                  cb_kwargs=kwargs,
                                  )


    def get_tag_info(self, jsn):
        tag_info = next(self.get_json_xpath(jsn, self._json_xpath["tag_info"]))
        result = {}
        for key, value in tag_info.items():
            if not isinstance(value, dict):
                result.update({key: value})
        return result


    def get_json_xpath(self, jsn, key):
        for itm in parse(key).find(jsn):
            yield itm.value

    def js_data_extract(self, response):
        script = response.xpath(
            "//script[contains(text(), 'window._sharedData = ')]/text()"
        ).extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])
