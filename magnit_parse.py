from pathlib import Path
import requests
from urllib.parse import urljoin
import bs4
import pymongo
from pathlib import Path
import time
from datetime import datetime


class MagnitParse:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 "
                      "(Macintosh; Intel Mac OS X 10.16; rv:85.0) "
                      "Gecko/20100101 Firefox/85.0",
    }
    attempts_count = 5

    def __init__(self, start_url, db_client):
        self.start_url = start_url
        self.db = db_client["gb_data_mining_16_02_2021"]

    @staticmethod
    def parse_date(date_in: str, second=False) -> datetime:
        """Ожидается строка в формате c 01 января до 02 февраля
        Если дата меньше текущей и second=True,
        считается, что это следующий год"""

        date_in = date_in.strip()

        if date_in.lower().startswith('только '):
            date_in = date_in.lower().replace('только ', '')
        else:
            if not second:
                date_in = date_in.split('\nдо')[0][2:]
            else:
                date_in = date_in.split('\nдо')[1]

        months = {
            'января': '01',
            'февраля': '02',
            'марта': '03',
            'апреля': '04',
            'мая': '05',
            'июня': '06',
            'июля': '07',
            'августа': '08',
            'сентября': '09',
            'октября': '10',
            'ноября': '11',
            'декабря': '12'
        }
        year = str(datetime.now().year)
        month = months.get(date_in.split()[1].strip())
        day = date_in.split()[0].strip()
        iso_date = f'{year}-{month}-{day}'
        if second and datetime.fromisoformat(iso_date) < datetime.now():
            year = str(datetime.now().year + 1)
            iso_date = f'{year}-{month}-{day}'
            return datetime.fromisoformat(iso_date)

        return datetime.fromisoformat(iso_date)

    @staticmethod
    def check_price(price_tag: bs4.Tag, class_):
        price = price_tag.find('div', class_=class_) \
            .text.strip().replace('\n', '.')
        try:
            return float(price)
        except ValueError:
            return None

    @staticmethod
    def write_log(content: str, filename: str = 'error.log'):
        log_path = Path(__file__).parent.joinpath(filename)
        with open(log_path, 'a') as f:
            return f.write(content + '\n')

    def _get_response(self, url, params: dict = None):
        attempts = 0
        while True:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response
            attempts += 1
            if attempts >= self.attempts_count:
                self.write_log(f'Превышено максимальное количество '
                               f'попыток подключения '
                               f'({self.attempts_count}) для адреса '
                               f'{self.start_url} ошибка: '
                               f'{response.status_code}')
                print('Ошибка загрузки страницы, см. логи')
                exit(1)
            time.sleep(0.5)
            return response

    def _get_soup(self, url):
        response = self._get_response(url)
        try:
            soup = bs4.BeautifulSoup(response.text, "lxml")
            return soup
        except (TypeError, AttributeError) as e:
            e_msg = f'Ошибка обработке bs4 ({e}),' \
                    f' передано: {str(response)}'
            print('Ошибка при обработке bs4, см. логи')
            self.write_log(e_msg)
        exit(1)

    def _template(self):
        return {
            "url": lambda a: urljoin(self.start_url, a.attrs.get("href")),
            "promo_name": lambda a: a.find("div", attrs={"class": "card-sale__header"}).text,
            "title": lambda a: a.find("div", attrs={"class": "card-sale__title"}).text,

            "old_price": lambda a: self.check_price(a, 'label__price_old'),

            "new_price": lambda a: self.check_price(a, 'label__price_new'),

            "image_url": lambda a: urljoin(self.start_url,
                                           a.find('img', class_='lazy').attrs.get("data-src")),

            "date_from": lambda a: self.parse_date(
                a.find('div', class_='card-sale__date').text),

            "date_to": lambda a: self.parse_date(
                a.find('div', class_='card-sale__date').text, True)

        }

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_a in catalog.find_all("a", recursive=False):
            if 'card-sale_banner' in product_a.get_attribute_list('class'):
                continue
            product_data = self._parse(product_a)
            self.save(product_data)

    def _parse(self, product_a: bs4.Tag) -> dict:
        product_data = {}
        for key, funk in self._template().items():
            try:
                product_data[key] = funk(product_a)
            except AttributeError:
                pass

        return product_data

    def save(self, data: dict):
        collection = self.db["magnit"]
        collection.insert_one(data)
        # print(1)


if __name__ == "__main__":
    target_url = "https://magnit.ru/promo/"
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParse(target_url, db_client)
    parser.run()
