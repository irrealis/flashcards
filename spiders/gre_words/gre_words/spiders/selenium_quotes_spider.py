import scrapy
from scrapy_selenium import SeleniumRequest

class SeleniumQuotesSpider(scrapy.Spider):
  name = "selenium_quotes"

  def start_requests(self):
    urls = [
      'http://quotes.toscrape.com/page/1/',
      'http://quotes.toscrape.com/page/2/',
    ]
    for url in urls:
      yield SeleniumRequest(url = url, callback = self.parse)

  def parse(self, response):
    print(response.meta['driver'].title)
    page = response.url.split("/")[-2]
    filename = 'quotes-%s.html' % page
    with open(filename, 'wb') as f:
      f.write(response.body)
    self.log('Saved file %s' % filename)

