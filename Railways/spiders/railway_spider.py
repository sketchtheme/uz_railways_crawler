import scrapy
import datetime
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags

class Article(scrapy.Item):
    url = scrapy.Field()  # URL of the article
    title = scrapy.Field()  # Title of the article
    text = scrapy.Field()  # Text of the article
    access_date = scrapy.Field()  # Date when the article was accessed
    creation_date = scrapy.Field()  # Date when the article was created
    category = scrapy.Field()  # Category of the article

class ArticleLoader(ItemLoader):
    default_output_processor = TakeFirst()

    title_in = MapCompose(remove_tags, str.strip)
    title_out = TakeFirst()

    text_in = MapCompose(remove_tags, str.strip)
    text_out = Join('\n')

class RailwaySpider(scrapy.Spider):
    name = 'railways'
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
    }

    writing_systems = {
        'uz_lat': 'uz/',
        'uz_cyr': 'uz/', # I couldn't find cyrillic uzbek
        'rus': 'ru/',
        'eng': 'en/'
    }

    def __init__(self, ws='uz_lat', **kwargs):
        self.ws = ws
        self.page_no = 0
        self.start_urls = [f'https://railway.uz/{self.writing_systems[self.ws]}informatsionnaya_sluzhba/novosti/']
        super().__init__(**kwargs)

    def parse(self, response):
        news_links = response.css('a.full-link::attr(href)').getall()
        yield from response.follow_all(news_links, self.parse_item)
        next_page_url = response.css('a.more-button::attr(href)').get()
        if next_page_url:
            self.page_no += 1
            yield scrapy.Request(url=response.urljoin(next_page_url), callback=self.parse)

    def parse_item(self, response):
        a = ArticleLoader(item=Article(), response=response)
        a.add_value('url', response.url)
        a.add_value('title', response.css('h3.inner-content__title::text').get())
        a.add_value('text', response.css('p[style="text-align: justify;"]::text').getall())
        a.add_value('creation_date', response.css('time.news-info__time::attr(datetime)').get())
        a.add_value('access_date', datetime.datetime.now().strftime("%Y-%m-%d")) # strftime("%Y-%m-%d %H:%M:%S")
        yield a.load_item()
