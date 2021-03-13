from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose

from gb_parse.items import GbAutoYoulaItem
from urllib.parse import unquote
import json
import base64


def get_characteristics(item) -> dict:
    selector = Selector(text=item)
    return {
        "name": selector.xpath(
            '//div[contains(@class, "AdvertSpecs_label")]/text()'
        ).extract_first(),
        "value": selector.xpath(
            '//div[contains(@class, "AdvertSpecs_data")]//text()'
        ).extract_first(),
    }


def clear_price(item: list) -> str:
    return item[0].replace("\u2009", "")


def get_json(data: str) -> json:
    result = ''
    try:
        result = json.loads(unquote(data.split('("')[1].split('")')[0]))
    except IndexError:
        pass
    return result


def list_search(lst: list, sub: str, pos: int) -> str:
    for i, itm in enumerate(lst):
        if type(itm) == list:
            result = list_search(itm, sub, pos)
            if result:
                return result
        else:
            if itm == sub:
                return lst[i + pos]


def get_author_url(user_id: str) -> str:
    return 'https://youla.ru/user/' + user_id


def base64_decode(s: str):
    base64_bytes = s.encode('ascii')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('ascii')


def list_search_user_id(item):
    result = get_json(item[0])
    result = list_search(result, 'avatar', -1)
    result = get_author_url(result)
    return result


def list_search_phone(item):
    result = get_json(item[0])
    result = list_search(result, 'phone', 1)
    result = base64_decode(base64_decode(result))
    return result


class AutoyoulaLoader(ItemLoader):
    default_item_class = GbAutoYoulaItem
    url_out = TakeFirst()
    title_out = TakeFirst()
    price_out = clear_price
    characteristics_out = MapCompose(get_characteristics)
    description_out = TakeFirst()
    author_out = list_search_user_id
    phone_out = list_search_phone
