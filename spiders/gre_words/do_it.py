from scrapy_selenium import SeleniumRequest

import time

fetch(SeleniumRequest(url = 'https://www.vocabulary.com/account/lists/'))
time.sleep(12)
#request
#response
#response.css('list-list')
#response.body
#response.selector.css('table')
#response.css('table')
#response.css('table#list-list')
#response.css('table.list-list')
#response.css('table.list-list > td')
#response.css('table.list-list td')
#response.css('table.list-list td a')
#response.css('table.list-list td a').extract()
#response.css('table.list-list td a').text
#response.css('table.list-list td a').text()
#response.css('table.list-list td a').extract()
#response.css('table.list-list td a::text()').extract()
#response.css('table.list-list td a::text()')
#response.css('table.list-list td a::text')
#response.css('table.list-list td a').extract()
#response.css('table.list-list td a::attr(href)')
#response.css('table.list-list td a::attr(href)').extract_first()
#response.css('table.list-list td a::attr(href)').extract()
#response.css('table.list-list td a::text').extract()
#response.css('table.list-list td a')
#response.css('table.list-list td a')[0]
#response.css('table.list-list td a')[0].css('::text')
#response.css('table.list-list td a')[0].css('::text').extract()
#response.css('table.list-list td a')[0].css('::attr(href)').extract()
#reponse.follow('/lists/185604')
#response.follow('/lists/185604')
#x = response.follow('/lists/185604')
#type(x)
#response.css('table.list-list td a')[0].css('::attr(href)').extract_first()
#next_page = response.css('table.list-list td a')[0].css('::attr(href)').extract_first()
#fetch(SeleniumRequest(url = next_page))
##fetch(SeleniumRequest(url = 'https://www.vocabulary.com/{}'.format(next_page)))
next_page = response.css('table.list-list td a')[0].css('::attr(href)').extract_first()
fetch(SeleniumRequest(url = 'https://www.vocabulary.com{}'.format(next_page)))
#response.css('.wordlist')
#response.css('.wordlist li')
#response.css('.wordlist li')[0]
#response.css('.wordlist li')[0].css(::attr(freq))
#response.css('.wordlist li')[0].css('::attr(freq)')
#response.css('.wordlist li')[0].css('::attr(freq)').extract_first()
#entry = response.css('.wordlist li')[0]
#entry.css('::attr(freq)').extract_first()
#entry.css('a.word::text').extract_first()
entry = response.css('.wordlist li')[0]
word = entry.css('a.word::text').extract_first()
freq = entry.css('::attr(freq)').extract_first()
word_page = entry.css('::attr(href)').extract_first()
word, freq, word_page


