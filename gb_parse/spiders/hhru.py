import scrapy

from gb_parse.loaders import HhruVacancyLoader, HhruEmployerLoader


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    start_urls = ['https://chita.hh.ru/search/'
                  'vacancy?schedule=remote&L_profession_id=0&area=113']

    _nav_xpath = {
        "vacancy": "//a[contains(@class, 'HH-VacancyActivityAnalytics-Vacancy')]/@href",
        "employer": "//div[@class='vacancy-serp-item__meta-info-company']//"
                    "a[contains(@class, 'bloko-link')]/@href",
        "pagination": "//div[@data-qa='pager-block']//"
                      "a[contains(@class, 'HH-Pager-Control')]/@href",
        "emp_vacancies": "//div[@class='employer-sidebar-content']"
                         "//a[@data-qa='employer-page__employer-vacancies-link']/@href",
    }

    _vacancy_xpath = {
        "title": "//div[@class='vacancy-title']/h1[@class='bloko-header-1']/text()",
        "salary": "//div[@class='vacancy-title']/p[@class='vacancy-salary']//text()",
        "description": "//div[@class='vacancy-description']//"
                       "div[@class='g-user-content']//text()",  # Список
        "skills": "//div[@class='vacancy-section']//"
                  "div[contains(@data-qa, 'skills-element')]//text()",
        "employer_url": "//div[@class='vacancy-company__details']/"
                        "a[@class='vacancy-company-name']/@href"
    }

    _employer_xpath = {
        "title": "//div[@class='company-header']//"
                 "span[@class='company-header-title-name']/text()",
        "service": "//div[@class='employer-sidebar']//"
                   "div[text()='Сферы деятельности']/../p/text()",  # Строка через запятую
        "description": "//div[@class='company-description']/"
                       "div[@class='g-user-content']//text()",  # Список
        "site_url": "//div[@class='employer-sidebar']//"
                    "a[@data-qa='sidebar-company-site']/@href"
    }

    def _get_follow(self, response, select_str, callback, **kwargs):
        for link in response.xpath(select_str):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):
        print(1)
        yield from self._get_follow(response, self._nav_xpath["vacancy"], self.vacancy_parse)
        yield from self._get_follow(response, self._nav_xpath["employer"], self.employer_parse)
        yield from self._get_follow(response, self._nav_xpath["pagination"], self.parse)

    def vacancy_parse(self, response, *args, **kwargs):
        loader = HhruVacancyLoader(response=response)
        loader.add_value("url", response.url)
        for key, selector in self._vacancy_xpath.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()

    def employer_parse(self, response, *args, **kwargs):
        loader = HhruEmployerLoader(response=response)
        loader.add_value("url", response.url)
        for key, selector in self._employer_xpath.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()
        yield from self._get_follow(
            response, self._nav_xpath["emp_vacancies"], self.parse)
