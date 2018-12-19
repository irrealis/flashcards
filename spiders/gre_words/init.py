import gre_words.db_interface as dbi

db_url = 'sqlite:///gre_words.sqlite'
engine = dbi.create_engine(db_url, echo = True)
print(dir())
#if 'session' not in dir():
if False:
  session = dbi.Session(engine)
  #dbi.metadata.create_all(engine)
  dbi.Base.prepare(engine, reflect=True)

