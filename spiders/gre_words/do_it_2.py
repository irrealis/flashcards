import gre_words.db_interface as dbi

db_url = 'sqlite:///gre_words.sqlite'
engine = dbi.create_engine(db_url, echo = True)
if 'session' not in dir():
  session = dbi.Session(engine)
  dbi.Base.prepare(engine, reflect=True)

vocab_185604 = dbi.get_or_create(session, dbi.Vocab,
  id = 185604,
  description = '800 high frequency words GRE',
)

#abdicate = dbi.get_or_create(session, dbi.Word,
#  word = 'abdicate',
#  short_blurb = '''Sometimes someone in power might decide to give up that power and step down from his or her position. When they do that, they abdicate their authority, giving up all duties and perks of the job.''',
#  long_blurb = '''The original meaning of the verb abdicate came from the combination of the Latin ab- "away" and dicare "proclaim." (Note that in the charming relationships between languages with common roots, the Spanish word for "he says" is dice, which comes directly from dicare.) The word came to refer to disowning one's children, and it wasn't until the 17th century that the first use of the word relating to giving up power or public office was recorded.''',
#  frequency = 1648.06,
#)
#vocab_185604.word_collection.append(abdicate)
#
#sense = dbi.get_or_create(session, dbi.Sense,
#  sense = 'give up, such as power, as of monarchs and emperors, or duties and obligations',
#)
#sense.word_collection.append(abdicate)
#
#renounce = dbi.get_or_create(session, dbi.Word, word = 'renounce')
#sense.word_collection.append(renounce)
#
#related_sense = dbi.get_or_create(session, dbi.Sense,
#  sense = 'leave (a job, post, or position) voluntarily',
#)
#give_up = dbi.get_or_create(session, dbi.Word, word = 'give_up')
#resign = dbi.get_or_create(session, dbi.Word, word = 'resign')
#vacate = dbi.get_or_create(session, dbi.Word, word = 'vacate')
#related_sense.word_collection.append(give_up)
#related_sense.word_collection.append(renounce)
#related_sense.word_collection.append(resign)
#related_sense.word_collection.append(vacate)
#
#session.commit()
#
#sense_relation = sense.add_type_of(related_sense)
#session.commit()
#
#sense.types
#related_sense.type_of
#sense.type_of
#related_sense.types

for entry in response.css('.wordlist li'):
  word_text = entry.css('a.word::text').extract_first()
  freq = entry.css('::attr(freq)').extract_first()
  word = dbi.get_or_create(session, dbi.Word, word = word_text, frequency = freq)
  vocab_185604.word_collection.append(word)

session.commit()

