import json
import scrapy
from jsonpath_ng import jsonpath, parse
from datetime import datetime
from random import randint

from gb_parse.loaders import GbInstaUserLoader, GbInstaFollowerLoader


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    _login_url = "https://www.instagram.com/accounts/login/ajax/"
    _tags_path = "/explore/tags/"
    _graphql_url = 'https://www.instagram.com/graphql/query/'

    _query_cache = {
        "posts": "9b498c08113f1e09617a1703c22b2f32",
        "followers": "5aefa9893005572d237da5068082d8d5",
        "following": "3dec7e2c57367ef3da3d987d89f9dbc8"
    }

    _json_xpath = {
        "post_node": "$..hashtag.edge_hashtag_to_media.edges[*].node",
        "first_page_node": "$..hashtag.edge_hashtag_to_media|"
                           "edge_hashtag_to_top_posts.edges[*].node",
        "next_page": "$..hashtag.edge_hashtag_to_media.page_info",
        "tag_info": "$..TagPage[0]..hashtag",
        "user_id": "$..ProfilePage..user.id",
    }

    def __init__(self, login, password, ig_users=None, tags=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.tags = tags if tags else []
        self.ig_users = ig_users if ig_users else []

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

                for ig_user in self.ig_users:
                    yield response.follow(f"/{ig_user}/", callback=self.user_parse,
                                          cb_kwargs={'ig_user': ig_user})

    def user_parse(self, response, ig_user, step=0, *args, **kwargs):
        jsn = self.js_data_extract(response)
        user_id = next(self.get_json_xpath(jsn, self._json_xpath["user_id"]))
        loader = self.add_user(user_id, ig_user, step)
        referer = response.urljoin(f"/{ig_user}/followers/")
        url = f'https://www.instagram.com/graphql/query/?query_hash=' \
              f'{self._query_cache["followers"]}&variables={{"id":"{user_id}",' \
              f'"include_reel":true,"fetch_mutual":true,"first":50}}'
        yield response.follow(url,
                              headers={"X-CSRFToken": jsn["config"]["csrf_token"],
                                       "Referer": referer},
                              callback=self.get_followers,
                              cb_kwargs=dict(ig_user=ig_user, ig_user_id=user_id,
                                             xcrf=jsn["config"]["csrf_token"],
                                             loader=loader, step=step)
                              )


    def add_user(self, user_id, user_name, step):
        loader = GbInstaUserLoader()
        loader.add_value("user_id", user_id)
        loader.add_value("user_name", user_name)
        loader.add_value("step", step)
        return loader

    def add_follower(self, follower_id, loader, field):
        loader.add_value(field, {"user_id": follower_id})
        return loader

    def get_follow_link(self, user_id, end_cursor, q_type='followers', first=50):
        if not self._query_cache.get(q_type, 0):
            return None
        url = f'https://www.instagram.com/graphql/query/?query_hash=' \
              f'{self._query_cache[q_type]}&variables={{"id":"{user_id}",' \
              f'"include_reel":true,"fetch_mutual":true,"first":{first},' \
              f'"after": "{end_cursor}"}}'
        return url

    def get_followers(self, response, ig_user, ig_user_id, xcrf, loader, step):
        jsn = json.loads(response.text)
        for itm in self.get_json_xpath(jsn, "$..edge_followed_by..edges[*].node"):
            # yield self.add_user(itm.get("id"), itm.get("username"))
            loader = self.add_follower(itm.get("id"), loader, "followers")

        if next(self.get_json_xpath(jsn, "$..edge_followed_by..has_next_page")):
            referer = response.urljoin(f"/{ig_user}/followers/")
            end_cursor = next(self.get_json_xpath(jsn, "$..edge_followed_by..end_cursor"))
            url = self.get_follow_link(ig_user_id, end_cursor)
            yield response.follow(url, headers={"X-CSRFToken": xcrf, "Referer": referer},
                                  callback=self.get_followers,
                                  cb_kwargs=dict(ig_user=ig_user, ig_user_id=ig_user_id, xcrf=xcrf,
                                                 loader=loader, step=step)
                                  )
        else:
            url = f'https://www.instagram.com/graphql/query/?query_hash=' \
                  f'{self._query_cache["following"]}&variables={{"id":"{ig_user_id}",' \
                  f'"include_reel":true,"fetch_mutual":true,"first":50}}'
            yield response.follow(url,
                                  headers={"X-CSRFToken": xcrf},
                                  callback=self.get_following,
                                  cb_kwargs=dict(ig_user=ig_user, ig_user_id=ig_user_id, xcrf=xcrf,
                                                 loader=loader, step=step)
                                  )

    def get_following(self, response, ig_user, ig_user_id, xcrf, loader, step):
        jsn = json.loads(response.text)
        for itm in self.get_json_xpath(jsn, "$..edge_follow..edges[*].node"):
            # yield self.add_user(itm.get("id"), itm.get("username"))
            # loader = self.add_follower(itm.get("id"), loader, step, "followed")
            if not itm.get("is_private") and\
                    {'user_id': itm.get("id")} in loader._values['followers']:
                loader = self.add_follower(itm.get("id"), loader, "handshakes")
                url = response.urljoin(f"/{itm.get('username')}/")
                yield response.follow(url, callback=self.user_parse,
                                      cb_kwargs={'ig_user': itm.get('username'),
                                                 "step": step+1})

        if next(self.get_json_xpath(jsn, "$..edge_follow..has_next_page")):
            referer = response.urljoin(f"/{ig_user}/following/")
            end_cursor = next(self.get_json_xpath(jsn, "$..edge_follow..end_cursor"))
            url = self.get_follow_link(ig_user_id, end_cursor)
            yield response.follow(url, headers={"X-CSRFToken": xcrf, "Referer": referer},
                                  callback=self.get_followers,
                                  cb_kwargs=dict(ig_user=ig_user, ig_user_id=ig_user_id, xcrf=xcrf,
                                                 loader=loader, step=step)
                                  )
        else:
            yield loader.load_item()

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
