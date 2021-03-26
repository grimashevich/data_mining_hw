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
INST_LOGIN = 'brianatrumbo604'
INST_PASSWORD = "#PWD_INSTAGRAM_BROWSER:10:1615966838:AaFQANLJMEq" \
                "KGX419MK0JDoLZ6TlF1TqPQabk7IaLwnlb8kdSyfMMVm43rfw" \
                "jBbrIszueG1L0voy6Qtj8JoignmwrBSwECI7NY7mZ0NYj2LSxKGL" \
                "jdR29k6ixRscuV89gREYdzKXcCzLB0GC"

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
