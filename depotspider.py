import scrapy
from urllib.parse import urlparse
from scrapy.spiders import SitemapSpider, Rule
from scrapy.linkextractors import LinkExtractor
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import requests
from bs4 import BeautifulSoup

USER_AGENT = USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'

class Spider(SitemapSpider):
    name = 'depot_spider'
    sitemap_urls = ['https://www.saatva.com/sitemap.xml']

    def __init__(self, *args, **kwargs):
        super(Spider, self).__init__(*args, **kwargs)

        self.client = pymongo.MongoClient('mongodb+srv://user1:test123@homedepot.3p0igbw.mongodb.net/?retryWrites=true&w=majority')
        self.db = self.client['homedepot']
        self.collection = self.db['depotpdp']
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    def closed(self, reason): # close mongodb
        self.client.close()

    def save(self, url, name, category, dimensions, price, rating):
        data = {
            'url': url,
            'name': name,
            'dimensions': dimensions,
            'price': price,
            'rating': rating,
            'category': category
        }
        print(data)
        try:
            self.collection.insert_one(data)
            print('Data saved to MongoDB successfully.')
        except Exception as e:
            print('Error saving data to MongoDB:', str(e))

    def parse(self, response):
        if '/mattresses/' or '/furniture/' or '/bedding/' in response.url:
            soup = BeautifulSoup(response.body, 'html.parser')
            url = response.url
            name = soup.select_one('.productPanel__headingTitle').text.strip()
            try:
                try:
                    dimensions = soup.selectone('.furnitureOverview__dimensions--description').text.strip()
                except AttributeError and TypeError:
                    dimensions_title = soup.find('span', class_='specsFaqsAccordion__title', text='Dimensions')
                    if dimensions_title:
                        dimensions_content = dimensions_title.find_parents('div', class_='accordion-module__item-83a')[0].find_next_sibling('div', class_='accordion-module__content-22f')
                        if dimensions_content:
                            dimensions = dimensions_content.get_text(strip=True)
            except UnboundLocalError:
                dimensions = "Not Found"


            price = soup.select_one('.smallPriceDisplay__finalPrice').text.strip()

            try:
                category = soup.select_one('.breadcrumbBar__item:nth-of-type(2)').text.strip()
            except:
                parsed_url = urlparse(url)
                path = parsed_url.path
                segments = path.split("/")
                category = segments[1]

            try:
                reviews_num = soup.select_one('.reviews-qa-label')
                reviews_num_fin = reviews_num.get_text(strip=True).split()[0]
                if reviews_num_fin > 0:
                    rating = soup.select_one('.star-rating')['title']
                else:
                    rating = "Not Rated"
            except:
                rating = "Not Rated"

            try:
                yield {
                    'url': url,
                    'name': name,
                    'category': category,
                    'dimensions': dimensions,
                    'price': price,
                    'rating': rating
                }
                self.save(url, name, category, dimensions, price, rating)  # save to db
            except UnboundLocalError:
                yield {
                    'url': url,
                    'name': name,
                    'category': category,
                    'dimensions': "Not Found",
                    'price': price,
                    'rating': rating
                }
                self.save(url, name, category, "Not Found", price, rating) # save to db

    def parse_sitemap(self, response):
        soup = BeautifulSoup(response.text, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        for url in urls:
            yield response.follow(url, callback=self.parse)

    def start_requests(self):
        for url in self.sitemap_urls:
            yield scrapy.Request(url, callback=self.parse_sitemap)

    rules = [Rule(LinkExtractor(allow=r'/p/'), callback='parse', follow=True),]
