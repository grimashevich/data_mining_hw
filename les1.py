import time
import json
from pathlib import Path
import requests


class Parse5Ka:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 "
                      "(Macintosh; Intel Mac OS X 10.16; rv:85.0) "
                      "Gecko/20100101 Firefox/85.0",
    }
    attempts_count = 5

    def __init__(self, url: str, products_path: Path):
        self.start_url = url
        self.products_path = products_path

    def _write_log(self, content: str, filename: str = 'Parse5ka.log'):
        log_path = self.products_path.parent.joinpath(filename)
        with open(log_path, 'a') as f:
            return f.write(content + '\n')

    def _get_response(self, url, params: dict = None):
        params = {} if params is None else params
        attempts = 0
        while True:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response
            attempts += 1
            if attempts >= self.attempts_count:
                self._write_log(f'Превышено максимальное количество '
                                f'попыток подключения '
                                f'({self.attempts_count}) для адреса '
                                f'{self.start_url}')
                print('Ошибка загрузки страницы, см. логи')
                return False
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            product_path = self.products_path.joinpath(
                f"{product['id']}.json")
            self._save(product, product_path)

    def _parse(self, url, params: dict = None):
        params = {} if params is None else params
        while url:
            response = self._get_response(url, params)
            data = response.json()
            url = data["next"]
            yield data['results']

    @staticmethod
    def _save(data: dict, file_path):
        jdata = json.dumps(data, ensure_ascii=False)
        file_path.write_text(jdata, encoding="UTF-8")


class Parse5kaCats(Parse5Ka):

    def __init__(self, cats_url: str, url: str, products_path: Path):
        super().__init__(url, products_path)
        self.cats_url = cats_url

    def _get_cat(self):
        response = super()._get_response(self.cats_url)
        for cat in response.json():
            yield cat

    def run(self):
        for cat in self._get_cat():
            print(f"{cat['parent_group_name']} | ", end='')
            cat_json = {'name': cat['parent_group_name'],
                        'code': cat['parent_group_code'],
                        'products': []}
            cat_id = cat['parent_group_code']
            save_path = self.products_path.joinpath(
                cat_id + '.json')
            for json_part in super()._parse(self.start_url,
                                            {'records_per_page': '20',
                                             'categories': cat_id}):
                cat_json['products'].extend(json_part)
                print('.', end=' ')
            super()._save(cat_json, save_path)
            print('|')


if __name__ == "__main__":
    catalogs_url = 'https://5ka.ru/api/v2/categories/'
    goods_url = "https://5ka.ru/api/v2/special_offers/"
    save_path_cats = Path(__file__).parent.joinpath("products_by_cats")
    if not save_path_cats.exists():
        save_path_cats.mkdir()
    p = Parse5kaCats(catalogs_url, goods_url, save_path_cats)
    p.run()
