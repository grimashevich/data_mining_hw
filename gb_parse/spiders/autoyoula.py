import scrapy
from urllib.parse import unquote
import json
import base64
import pymongo


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]
    _css_selectors = {
        "brands": "div.TransportMainFilters_brandsList__2tIkv "
                  ".ColumnItemList_item__32nYI a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "car": "article.SerpSnippet_snippet__3O1t2 .SerpSnippet_titleWrapper__38bZM a.blackLink",
        "spec_block": "div.AdvertCard_specs__2FEHc div.AdvertSpecs_row__ljPcX",
        "spec_title": "div.AdvertSpecs_label__2JHnS::text",
        "spec_value": "div.AdvertSpecs_data__xK2Qx::text",
        "car_photos": "div.PhotoGallery_block__1ejQ1 "
                      "img.PhotoGallery_photoImage__2mHGn::attr(src)",
        "car_description": "div.AdvertCard_description__2bVlR "
                           "div.AdvertCard_descriptionInner__KnuRi::text",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_client = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = self.db_client["autoyoula_parse"]

    def _save_to_db(self, data: dict):
        collection = self.db["cars"]
        collection.insert_one(data)
        print('saved')

    @staticmethod
    def _list_search(lst: list, sub: str, pos=-1):
        for i, itm in enumerate(lst):
            if type(itm) == list:
                result = AutoyoulaSpider._list_search(itm, sub, pos)
                if result:
                    return result
            else:
                if itm == sub:
                    return lst[i + pos]

    @staticmethod
    def _list_search_list(lst: list, sub: dict):
        for itm in lst:
            if type(itm) == list and len(itm) >= len(sub):
                is_here = all([sub[key] == itm[key] for key in sub.keys()])
                if is_here:
                    return lst
                else:
                    result = AutoyoulaSpider._list_search_list(itm, sub)
                    if result:
                        return result

    @staticmethod
    def base64_decode(s: str, cnt=1):
        msg = s
        for i in range(cnt):
            base64_bytes = msg.encode('ascii')
            message_bytes = base64.b64decode(base64_bytes)
            msg = message_bytes.decode('ascii')
        return msg

    def _get_spec_value(self, response, selector):
        """Если не получается вернуть значение по основному селектору,
        пробует получить его из вложенной ссылки"""
        value = response.css(self._css_selectors[selector]).extract_first()
        if not value:
            new_selector = self._css_selectors[selector].replace("::text", '') \
                           + " a::text"
            value = response.css(new_selector).extract_first()
        return value

    def _get_follow(self, response, select_str, callback, **kwargs):
        for a in response.css(select_str):
            link = a.attrib.get("href")
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):
        yield from self._get_follow(response, self._css_selectors["brands"], self.brand_parse)

    def brand_parse(self, response, *args, **kwargs):

        yield from self._get_follow(response, self._css_selectors["pagination"], self.brand_parse)

        yield from self._get_follow(response, self._css_selectors["car"], self.car_parse)

    def car_parse(self, response):
        title = response.css(".AdvertCard_advertTitle__1S1Ak::text").extract_first()
        spec = {}
        for itm in response.css(self._css_selectors["spec_block"]):
            spec.update(
                {itm.css(self._css_selectors["spec_title"]).extract_first():
                     self._get_spec_value(itm, "spec_value")})
        description = response.css(self._css_selectors["car_description"]).extract_first()

        transit_state = unquote(response.css("script")[-6].extract().split('("')[1].split('")')[0])
        transit_state = json.loads(transit_state)
        user_id = AutoyoulaSpider._list_search(transit_state, 'avatar')
        user_url = 'https://youla.ru/user/' + user_id
        photos = []
        try:
            photos_list = transit_state[1][17][1][29][1]
            for itm in photos_list:
                photo = None
                for size in ('big', 'large', 'medium', 'small'):
                    photo = AutoyoulaSpider._list_search(itm, size, 1)
                    if photo:
                        photos.append(photo)
                        break
        except IndexError as e:
            print('Местонахождение фото в transit_state не '
                  'найдено или изменилось \n' + str(e))

        phone = AutoyoulaSpider.base64_decode(AutoyoulaSpider._list_search(
            transit_state, 'phone', 1), 2)

        result = {
            "title": title,
            "spec": spec,
            "description": description,
            "user_url": user_url,
            "photos": photos,
            "phone": phone
        }
        self._save_to_db(result)
