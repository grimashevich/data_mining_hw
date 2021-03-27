import os
# import dotenv

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
from gb_parse.spiders.hhru import HhruSpider
from gb_parse.spiders.instagram import InstagramSpider

# TODO Исправить, если dotnev удастся установить
# Не устанавливается нигде: Ни в Linux, ни в Windows.
# Судя по логам, какие-то проблемы в загрузке доп. пакетов
# Это фейковый instagram аккаунт специально для ДЗ
INST_LOGIN = 'debwhitworth333'
INST_PASSWORD = "#PWD_INSTAGRAM_BROWSER:10:1616837702:AStQAHW6mk2THL3kRqv+Y39enX+GK4TdGLtXkGpdyWx2jrNwH" \
                "gKxvjyGHda/lxiEVArx1I92PfJNw1G0nah8gMtMSMZOTZk5R3HOsbCNoSj9x5Mz47tWTJ3bAq2gt97c7+FM/d/98TjdSpcIIA=="

if __name__ == "__main__":
    ig_users = ['valeriyaar']
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
        ig_users=ig_users
    )
    crawler_proc.start()
