import typing
import requests
from urllib.parse import urljoin
import bs4
from database.db import Database
from datetime import datetime
import time
from pathlib import Path


class GbBlogParse:
    attempts_count = 5

    def __init__(self, start_url, database: Database):
        self.db = database
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = []

    @staticmethod
    def write_log(content: str, filename: str = 'error.log'):
        log_path = Path(__file__).parent.joinpath(filename)
        with open(log_path, 'a') as f:
            return f.write(content + '\n')

    def _get_response(self, url):
        attempts = 0
        while True:
            response = requests.get(url)
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

    def _get_soup(self, url):
        resp = self._get_response(url)
        soup = bs4.BeautifulSoup(resp.text, "lxml")
        return soup

    def __create_task(self, url, callback, tag_list):
        for link in set(
                urljoin(url, href.attrs.get("href")) for href in tag_list if href.attrs.get("href")
        ):
            if link not in self.done_urls:
                task = self._get_task(link, callback)
                self.done_urls.add(link)
                self.tasks.append(task)

    def _parse_feed(self, url, soup) -> None:
        ul = soup.find("ul", attrs={"class": "gb__pagination"})
        self.__create_task(url, self._parse_feed, ul.find_all("a"))
        self.__create_task(
            url, self._parse_post, soup.find_all("a", attrs={"class": "post-item__title"})
        )

    def _parse_post(self, url, soup) -> dict:
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        post_id = soup.find("comments").attrs.get("commentable-id")
        data = {
            "post_data": {
                "url": url,
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                "post_date": datetime.fromisoformat(
                    soup.find("time", attrs={"class": "text-md text-muted m-r-md"}). \
                        attrs.get("datetime")),
                "first_img": soup.find("div", attrs={"class": "blogpost-content"}). \
                    find("img").attrs.get("src") if \
                    soup.find("div", attrs={"class": "blogpost-content"}).find("img") else None
            },
            "author": {
                "name": author_name_tag.text,
                "url": urljoin(url, author_name_tag.parent.attrs.get("href")),
            },
            "tags": [
                {"name": a_tag.text, "url": urljoin(url, a_tag.attrs.get("href"))}
                for a_tag in soup.find_all("a", attrs={"class": "small"})
            ],
            "comments": [post_comment for post_comment in self.get_comments(post_id)]
        }
        return data

    def _get_task(self, url, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        return task

    def _parse_comments(self, comments: list, post_id: int):
        for value in comments:
            comment = value['comment']
            data = {
                "id": comment.get('id'),
                "post_id": post_id,
                "text": comment.get('body'),
                "parent_id": comment.get('parent_id'),
                "root_comment_id": comment.get('root_comment_id'),
                "author": {
                    "name": comment['user'].get('full_name'),
                    "url": comment['user'].get('url'),
                }
            }

            yield data
            yield from self._parse_comments(comment['children'], post_id)

    def get_comments(self, post_id: str, api_url=None):
        if not api_url:
            api_url = 'https://geekbrains.ru/api/v2/comments?' \
                      'commentable_type=Post&order=desc'
        api_url += '&commentable_id=' + post_id
        return self._parse_comments(self._get_response(api_url).json(),
                                    int(post_id))

    def run(self):
        self.tasks.append(self._get_task(self.start_url, self._parse_feed))
        self.done_urls.add(self.start_url)
        i = 0
        for task in self.tasks:
            result = task()
            if isinstance(result, dict):
                self.db.create_post(result)
            print('.', end='')
            i += 1
            if i % 100 == 0:
                print('')


if __name__ == "__main__":
    db = Database("sqlite:///gb_blog.db")
    parser = GbBlogParse("https://geekbrains.ru/posts", db)
    parser.run()
