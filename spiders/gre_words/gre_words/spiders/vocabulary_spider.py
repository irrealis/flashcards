import scrapy

class VocabularySpider(scrapy.Spider):
    name = "vocabulary"

    def start_requests(self):
        urls = [
            'https://www.vocabulary.com/lists/185684'
        ]
        for url in urls:
            yield scrapy.Request(url = url, callback = self.parse_start)

    def parse_start(self, response):
        wordlist = response.css('#wordlist li.entry')
        for word in wordlist:
            yield {
                'defined_word': word.css('a.word ::text').extract_first(),
                'short_definition': word.css('div.definition').extract_first(),
            }
        for word in wordlist[710:]:
            yield response.follow(word.css('a.word'), callback = self.parse_def)

    def parse_def(self, response):
        blurbed = response.css('.vocab.blurbed')
        yield {
            'blurbed_word': blurbed.css('h1.dynamictext ::text').extract_first(),
            'short_blurb': blurbed.css('p.short').extract_first(),
            'long_blurb': blurbed.css('p.long').extract_first(),
        }
