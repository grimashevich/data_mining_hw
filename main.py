import os
# import dotenv

from pymongo import MongoClient
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.hhru import HhruSpider
from gb_parse.spiders.instagram import InstagramSpider

# TODO Исправить, если dotnev удастся установить
# Не устанавливается нигде: Ни в Linux, ни в Windows.
# Судя по логам, какие-то проблемы в загрузке доп. пакетов
# Это фейковый instagram аккаунт специально для ДЗ
INST_LOGIN = 'helencook4858'
INST_PASSWORD = "#PWD_INSTAGRAM_BROWSER:10:1616925098:AZlQAFMghqIRC3SVTdmjvdSRWgviHWeHdvTwciz9vi7thZ5xJ2it" \
                "En/BuO0vACgWp0cs81yfU3LRv4HbVjkGoxlFUQxIjzzJo6RFeCzESs6Qv61j8ckQllIIH/uMhjsMz2YS+opjeBNctPW5"

USERS_TO_SEARCH = ['e_rtmn', 'jutlz']  # Пользователи, между которыми нужно найти цепочку рукопожатий


def find_handshakes():
    if len(USERS_TO_SEARCH) == 2:
        username = USERS_TO_SEARCH[1]
    else:
        return None
    result = []
    client = MongoClient()
    collection = 'GbInstaUser'
    db = client["gb_parse_16_02_2021"]
    if not db[collection].find_one({'user_name': username}):
        print('Не найдено')
        return None
    cur_user = db[collection].find_one({'user_name': username})
    step = cur_user['step']
    user_id = cur_user['user_id']
    result.append(cur_user['user_name'])
    while step > 0:
        cur_user = db[collection].find_one({'handshakes': {"user_id": user_id}, 'step': step - 1})
        if not cur_user:
            print('Не найдено')
            return None
        step = cur_user['step']
        user_id = cur_user['user_id']
        result.append(cur_user['user_name'])
    print('Найдена цепочка длиной: ', len(result)-1)
    print(result)
    return result


if __name__ == "__main__":
    ig_users = ['arla.nda']
    crawler_settings = Settings()
    crawler_settings.setmodule("gb_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    # crawler_proc.crawl(AutoyoulaSpider)
    # crawler_proc.crawl(HhruSpider)
    crawler_proc.crawl(
        InstagramSpider,
        # login=os.getenv("INST_LOGIN"),
        # password=os.getenv("INST_PASSWORD"),
        login=INST_LOGIN,
        password=INST_PASSWORD,
        # tags=tags,
        ig_users=[USERS_TO_SEARCH[0]]
    )
    crawler_proc.start()
    find_handshakes()
