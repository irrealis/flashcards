session.rollback()

#fetch(SeleniumRequest(url = 'https://www.vocabulary.com/account/lists/'))

#vocab_link_3 = response.css('table.list-list td a')[3]
#vocab_list_relurl = vocab_link_3.css('::attr(href)').extract_first()
#vocab_list_id = int(vocab_list_relurl.split('/')[-1])
#vocab_list_description = vocab_link_3.css('::text').extract_first().strip()
vocab_list = dbi.get_or_create(session, dbi.Vocab,
  id = vocab_list_id,
  description = vocab_list_description
)

#time.sleep(4)
#fetch(SeleniumRequest(url = 'https://www.vocabulary.com{}'.format(vocab_list_relurl)))

#entry = response.css('.wordlist li')[0]
#word_page = entry.css('::attr(href)').extract_first()
#word_text = entry.css('a.word::text').extract_first()
#freq = entry.css('::attr(freq)').extract_first()
#print("word_text: {}".format(word_text))
#word = dbi.get_or_create(session, dbi.Word, word = word_text)
#vocab_list.word_collection.append(word)
#session.commit()

for entry in response.css('.wordlist li'):
  word_text = entry.css('a.word::text').extract_first()
  freq = entry.css('::attr(freq)').extract_first()
  print("word_text: {}".format(word_text))
  word = dbi.get_or_create(session, dbi.Word, word = word_text)
  try:
    freq = float(freq)
  except ValueError:
    freq = float('nan')
  word.frequency = freq
  vocab_list.word_collection.append(word)
  #session.commit()

session.commit()
