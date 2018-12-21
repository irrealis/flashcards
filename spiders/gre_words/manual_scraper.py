import gre_words.db_interface as dbi

import scrapy as sp
import selenium as se
from selenium import webdriver
import selenium.webdriver.chrome.service as service
import selenium.webdriver.chrome.options as options
from selenium.webdriver.common.by import By as se_By
from selenium.webdriver.support.ui import WebDriverWait as se_WebDriverWait
from selenium.webdriver.support import expected_conditions as se_EC

import matplotlib as mp
import numpy as np
import pandas as pd
from scipy import stats as st
import matplotlib.pyplot as plt



import asyncio
import datetime as dt
#import logging
import time
import types

#alog = logging.getLogger("asyncio")
#alog.setLevel(logging.DEBUG)
#ach = logging.StreamHandler()
#ach.setLevel(logging.DEBUG)
#alog.addHandler(ach)


def get_session(echo = True):
  db_url = 'sqlite:///gre_words.sqlite'
  engine = dbi.create_engine(db_url, echo = echo)
  ssn = dbi.Session(engine)
  dbi.Base.prepare(engine, reflect=True)
  return ssn

def get_webdriver():
  opts = se.webdriver.chrome.options.Options()
  opts.binary_location = '/opt/google/chrome/google-chrome'
  opts.add_argument(
    'user-data-dir=/mnt/Work/Repos/irrealis/flashcards/spiders/google-chrome-config'
  )
  opts.to_capabilities()

  svc = se.webdriver.chrome.service.Service('/home/kaben/.local/bin/chromedriver-2.45.615279')
  svc.start()
  drv = se.webdriver.Remote(svc.service_url, opts.to_capabilities())
  return svc, drv


def get_ds():
  times = [
    "00:20:00",
    "00:20:40",
    "00:21:15",
    "00:22:27",
    "00:23:20",
    "00:24:23",
    "00:25:15",
    "00:26:06",
    "00:26:40",
    "00:27:26",
    "00:28:16",
    "00:29:54",
    "00:30:09",
    "00:30:59",
    "00:31:36",
    "00:32:18",
    "00:34:05",
    "00:35:03",
    "00:35:42",
    "00:36:47",
    "00:37:44",
    "00:38:21",
    "00:39:09",
    "00:40:17",
    "00:41:13",
    "00:42:07",
    "00:43:00",
    "00:43:47",
    "00:44:39",
    "00:45:18",
    "00:45:52",
    "00:46:30",
    "00:47:05",
    "00:47:52",
    "00:48:36",
    "00:49:22",
    "00:49:53",
    "00:50:40",
    "00:51:25",
    "00:52:09",
    "00:53:47",
    "00:54:45",
    "00:55:27",
    "00:56:27",
    "00:57:22",
    "00:58:05",
    "00:59:02",
    "00:59:50",
    "01:01:31",
    "01:02:15",
    "01:03:19",
    "01:04:05",
    "01:04:39",
    "01:05:37",
    "01:06:48",
    "01:07:03",
    "01:07:56",
    "01:09:03",
    "01:10:08",
    "01:11:01",
    "01:12:04",
    "01:13:20",
    "01:14:15",
    "01:15:48",
    "01:16:20",
    "01:17:06",
    "01:17:46",
    "01:18:37",
    "01:19:25",
    "01:19:57",
  ]
  dts = [dt.datetime.strptime(time, '%H:%M:%S') for time in times]
  ds = np.array([(b-a).seconds for (b,a) in zip(dts[1:], dts[:-1])])
  return ds


def get_kde(ds = None):
  if ds is None:
    ds = get_ds()
  dist = pd.DataFrame(ds)
  kde = st.gaussian_kde(ds)
  return kde


def get_hourly_schedule(start_dt = None, n = 4):
  if start_dt is None:
    start_dt = dt.datetime.now()
  s = [
    (
      start_dt + dt.timedelta(seconds = i*60*60 + 50*60),
      start_dt + dt.timedelta(seconds = (i+1)*60*60)
    )
    for i in range(n)
  ]
  return s
  
def get_rounded_hourly_schedule(n = 4):
  now = dt.datetime.now()
  hour = now.hour
  if 50 <= now.minute:
    hour += 1
  return get_hourly_schedule(
    dt.datetime(
      now.year,
      now.month,
      now.day,
      hour,
    ),
    n
  )
  
def get_minute_schedule(start_dt = None, n = 4):
  if start_dt is None:
    start_dt = dt.datetime.now()
  s = [
    (
      start_dt + dt.timedelta(seconds = i*60 + 50),
      start_dt + dt.timedelta(seconds = (i+1)*60)
    )
    for i in range(n)
  ]
  return s


def get_boundedsleep(kde, min_sleep_mu, min_sleep_sd):
  min_sleep_period = (min_sleep_mu + min_sleep_sd*st.norm().rvs(1))[0]
  samp_sleep_period = (kde.resample(1)[0])[0]
  if samp_sleep_period < min_sleep_period:
    print(" Clamping sleep period {} to {}".format(
      samp_sleep_period,
      min_sleep_period
    ))
  return max(samp_sleep_period, min_sleep_period)
  
  
def get_wakesleep(wake, period):
  next_wake = wake + dt.timedelta(seconds = period)
  now = dt.datetime.now()
  sleep_dt = next_wake - now
  reversecheck = next_wake - wake
  print(" Next wake: {}; interperiod: {} sec".format(
    next_wake.strftime('%H:%M:%S.%f'),
    period
  ))
  # It's possible the wake time is in the past, which we would have to fix.
  if sleep_dt < dt.timedelta(0):
    next_wake = now
    sleep_dt = dt.timedelta(0)
    print(" Next wake is in past; adusted: {}".format(
      next_wake.strftime('%H:%M:%S.%f')
    ))
  return next_wake, sleep_dt


def runtask(task):
  intertask_period = None
  if type(task) is types.GeneratorType:
    try:
      intertask_period = next(task)
    except StopIteration:
      pass
  else:
    intertask_period = task()
  return intertask_period


# Method to perform simulated problems on Vocabulary.com.
def work(task, schedule, break_sd = 154):
  print("\nSchedule:")
  print("{}".format(schedule))
  print("\nBreak standard deviation: {}".format(break_sd))
  print("\nStarting work.")

  # This loops over simulated study periods, each 50 minutes long with 10-minute breaks in between.
  for break_t, start_t in schedule:
    print('Starting new work session; next break at: {}, next start at: {}'.format(
      break_t.strftime('%H:%M:%S'),
      start_t.strftime('%H:%M:%S')
    ))

    # This loops over simulated vocabulary problems within a study period.
    wake = now = dt.datetime.now()
    while now < break_t:
      print("Awake; now: {}".format(now.strftime('%H:%M:%S.%f'))) 
      # Do stuff... then task decides when to start the subsequent task.
      intertask_period = runtask(task)
      if intertask_period is None:
        print(" No tasks left.")
        return

      wake, sleep_dt = get_wakesleep(wake, intertask_period)
      time.sleep(sleep_dt.total_seconds())
      now = dt.datetime.now()

    # This simulates the break between work periods.
    break_period = ((start_t - now).total_seconds() + break_sd*st.norm().rvs(1))[0]
    print("Break; now: {}, sleep {:.6f}s until about {}...".format(
      now.strftime('%H:%M:%S.%f'),
      break_period,
      start_t.strftime('%H:%M:%S'),
    ))
    wake, sleep_dt = get_wakesleep(wake, break_period)
    time.sleep(sleep_dt.total_seconds())

  print("Reached schedule end.")


async def work_async(task, schedule, break_sd = 154):
  print("\nSchedule:")
  print("{}".format(schedule))
  print("\nBreak standard deviation: {}".format(break_sd))
  print("\nStarting work.")

  # This loops over simulated study periods, each 50 minutes long with 10-minute breaks in between.
  for break_t, start_t in schedule:
    print('Starting new work session; next break at: {}, next start at: {}'.format(
      break_t.strftime('%H:%M:%S'),
      start_t.strftime('%H:%M:%S')
    ))

    # This loops over simulated vocabulary problems within a study period.
    wake = now = dt.datetime.now()
    while now < break_t:
      print("Awake; now: {}".format(now.strftime('%H:%M:%S.%f'))) 
      # Do stuff... then task decides when to start the subsequent task.
      intertask_period = runtask(task)
      if intertask_period is None:
        print(" No tasks left.")
        return

      wake, sleep_dt = get_wakesleep(wake, intertask_period)
      await asyncio.sleep(sleep_dt.total_seconds())
      now = dt.datetime.now()

    # This simulates the break between work periods.
    break_period = ((start_t - now).total_seconds() + break_sd*st.norm().rvs(1))[0]
    print("Break; now: {}, sleep {:.6f}s until about {}...".format(
      now.strftime('%H:%M:%S.%f'),
      break_period,
      start_t.strftime('%H:%M:%S'),
    ))
    wake, sleep_dt = get_wakesleep(wake, break_period)
    await asyncio.sleep(sleep_dt.total_seconds())

  print("Reached schedule end.")




async def simulation(
  to_do,
	schedule,
	kde,
  min_sleep_mu = 12.30987,
  min_sleep_sd = 2.23487,
  break_sd = 154,
):
  print("\nStarting simulation.")

  # This loops over simulated study periods, each 50 minutes long with 10-minute breaks in between.
  for break_t, start_t in schedule:
    print('Starting period; next break at: {}, next start at: {}'.format(
      break_t.strftime('%H:%M:%S'),
      start_t.strftime('%H:%M:%S')
    ))

    # This loops over simulated vocabulary problems within a study period.
    now = dt.datetime.now()
    while now < break_t:
      # Decide when we want to start the next simulated problem.
      min_sleep_period = (min_sleep_mu + min_sleep_sd*st.norm().rvs(1))[0]
      samp_sleep_period = (kde.resample(1)[0])[0]
      sleep_period = max(samp_sleep_period, min_sleep_period)
      wake = now + dt.timedelta(seconds = sleep_period)
      print("Awake; now: {}, min: {:.2f}s, samp: {:.2f}s, sleep: {:.6f}s".format(
        now.strftime('%H:%M:%S.%f'),
        min_sleep_period,
        samp_sleep_period,
        sleep_period,
      ))
      print(" Next wake: {}".format(wake.strftime('%H:%M:%S.%f')))

      # Do stuff...
      early_exit = False
      try:
        result = next(to_do)
        print("Result: {}".format(result))
      except StopIteration:
        early_exit = True
      if early_exit:
        print("No tasks left; returning.")
        return

      # Decide how long we need to sleep in order to awaken when planned.
      sleep_dt = wake - dt.datetime.now()
      await asyncio.sleep(sleep_dt.seconds + 1e-6*sleep_dt.microseconds)
      now = dt.datetime.now()

    # This simulates the break between study periods.
    break_period = ((start_t - dt.datetime.now()).seconds + break_sd*st.norm().rvs(1))[0]
    wake = now + dt.timedelta(seconds = break_period)
    print("Break; now: {}, sleep {:.6f}s until about {}...".format(
      now.strftime('%H:%M:%S.%f'),
      break_period,
      start_t.strftime('%H:%M:%S'),
    ))
    print(" Next wake: {}".format(wake.strftime('%H:%M:%S.%f')))
    sleep_dt = wake - dt.datetime.now()
    await asyncio.sleep(sleep_dt.seconds + 1e-6*sleep_dt.microseconds)

  print("Done; leaving simulation.")


def say_something():
  print("something...")


class SaySomething(object):
  def gen(self):
    for i in range(3):
      print("yielding...")
      yield i
      print("back...")
  def __call__(self):
    print("Something...")


class Scraper(object):
  def __init__(
    self,
    ssn,
    dbi,
    drv,
    study_kde,
    navigate_kde,
    min_nav_sleep_mu = 12.30987/2,
    min_nav_sleep_sd = 2.23487/2,
    min_sleep_mu = 12.30987,
    min_sleep_sd = 2.23487,
  ):
    self.ssn = ssn
    self.dbi = dbi
    self.drv = drv
    self.study_kde = study_kde
    self.nav_kde = navigate_kde
    self.mnsleep_mu = min_nav_sleep_mu
    self.mnsleep_sd = min_nav_sleep_sd
    self.msleep_mu = min_sleep_mu
    self.msleep_sd = min_sleep_sd
    
  def waitget_elem_by_linktext(self, text, timeout = 10):
    return se_WebDriverWait(self.drv, timeout).until(
      se_EC.presence_of_element_located(
        (se_By.LINK_TEXT, text)
      )
    )

  def waitget_elem_by_partiallinktext(self, text, timeout = 10):
    return se_WebDriverWait(self.drv, timeout).until(
      se_EC.presence_of_element_located(
        (se_By.PARTIAL_LINK_TEXT, text)
      )
    )

  def waitget_elem_by_css(self, text, timeout = 10):
    return se_WebDriverWait(self.drv, timeout).until(
      se_EC.presence_of_element_located(
        (se_By.CSS_SELECTOR, text)
      )
    )

  def get_mainpage(self):
    self.drv.get('https://www.vocabulary.com')
    yield get_boundedsleep(self.nav_kde, self.mnsleep_mu, self.mnsleep_sd)
  
  def get_listspage(self):
    button = self.waitget_elem_by_css('button.hamburger.menu')
    button.click()
    yield get_boundedsleep(self.nav_kde, self.mnsleep_mu, self.mnsleep_sd)
    a = self.waitget_elem_by_linktext('My Lists')
    a.click()
    yield get_boundedsleep(self.nav_kde, self.mnsleep_mu, self.mnsleep_sd)
  
  def get_listpage(self, partiallinktext):
    a = self.waitget_elem_by_partiallinktext(partiallinktext)
    a.click()
    yield get_boundedsleep(self.nav_kde, self.mnsleep_mu, self.mnsleep_sd)


  def examinelists(self):
    links = self.drv.find_elements_by_css_selector('table > tbody > tr > td > a')
    for a in links:
      list_description = a.text.split('\n')[0]
      link = a.get_attribute('href')
      list_id = link.split('/')[-1]
      vocab_list = self.dbi.get_or_create(self.ssn, self.dbi.Vocab,
        id = list_id
      )
      if vocab_list.description != list_description:
        print('updating list description from "{}" to "{}"...'.format(
          vocab_list.description,
          list_description,
        ))
        vocab_list.description = list_description
        self.ssn.commit()
      if not vocab_list.is_task_complete:
        print('is_task_complete: {}'.format(vocab_list.is_task_complete))


  def maybe_updatelists(self):
    yield from self.get_mainpage()
    yield from self.get_listspage()

    link_elements = self.drv.find_elements_by_css_selector('table > tbody > tr > td > a')
    # I can't use the original list of link elements for the iterations below,
    # because I'm switching pages, which makes the list stale.
    a_ct = len(link_elements)
    # So instead I iterate over the length of the list,
    print("entering loop...")
    for i in range(a_ct):
      # and on each iteration I refresh the list,
      self.waitget_elem_by_css('table > tbody > tr > td > a')
      link_elements = self.drv.find_elements_by_css_selector('table > tbody > tr > td > a')
      # and then get the ith link.
      a = link_elements[i]
      list_description = a.text.split('\n')[0]
      link = a.get_attribute('href')
      list_id = link.split('/')[-1]
      vocab_list = self.dbi.get_or_create(self.ssn, self.dbi.Vocab, id = list_id)
      print('maybe_updatelists: examining list "{}"...'.format(vocab_list))
      if vocab_list.description != list_description:
        vocab_list.description = list_description
        self.ssn.commit()
      if not vocab_list.is_task_complete:
        
        a.click()
        
        self.waitget_elem_by_css('.wordlist li')
        entries = self.drv.find_elements_by_css_selector('.wordlist li')
        for entry in entries:
          entry_a = entry.find_element_by_css_selector('a.word')
          word_text = entry_a.text
          freq = entry.get_attribute('freq')
          print('maybe_updatelists: processing word "{}"...'.format(word_text))
          word = self.dbi.get_or_create(self.ssn, self.dbi.Word, word = word_text)
          word.freq = freq
          vocab_list.word_collection.append(word)
        print('maybe_updatelists: hooray, updated list!')
        vocab_list.is_task_complete = True
        self.ssn.commit()
        print('maybe_updatelists: yielding...')

        period = get_boundedsleep(self.study_kde, self.msleep_mu, self.msleep_sd)
        yield period

        print('maybe_updatelists: back...')
        self.drv.back()
        sleep_period = (7 + 2*st.norm().rvs(1))[0]
        print('maybe_updatelists: sleeping {} sec...'.format(sleep_period))
        time.sleep(sleep_period)
      else:
        print('maybe_updatelists: nothing to do...')
        

  def process_related_sense_dds(self, instance, word, sense, sense_add_method):
    for related_sense_dd in instance.css('dd'):
      related_words = related_sense_dd.css('a.word::text').extract()
      if not related_words:
        # This section has no words, is probably used for JavaScript.
        continue
      related_sense_def = related_sense_dd.css('div.definition::text').extract_first()
      if related_sense_def:
        related_sense = self.dbi.get_or_create(self.ssn, self.dbi.Sense,
          sense = related_sense_def
        )
        for related_word_text in related_words:
          related_word = self.dbi.get_or_create(self.ssn, self.dbi.Word,
            word = related_word_text
          )
          related_sense.word_collection.append(related_word)
        self.ssn.commit()
        sense_add_method(related_sense)
        self.ssn.commit()
        print("      related sense: {}".format(related_sense_def))
      else:
        # If there's no text here, it means "use the sense, not the related sense."
        related_sense_def = '(no related sense)'
        for related_word_text in related_words:
          related_word = self.dbi.get_or_create(self.ssn, self.dbi.Word,
            word = related_word_text
          )
          sense.word_collection.append(related_word)
        self.ssn.commit()
        print("         this sense:")
      print("                     {}".format(related_words))

  
  def process_instance(self, instance, kind, word, sense):
    # Need to handle each kind of sense instance differently.
    if kind.startswith('synonyms'):
      sense_add_method = sense.add_synonym
    elif kind.startswith('antonyms'):
      sense_add_method = sense.add_antonym
    elif kind.startswith('types'):
      sense_add_method = sense.add_type
    elif kind.startswith('type of'):
      sense_add_method = sense.add_type_of
    self.process_related_sense_dds(instance, word, sense, sense_add_method)

  
  def examine_word(self, html):
    sel = sp.Selector(text = html)
    word_text = sel.css('.dynamictext::text').extract_first()
    short_blurb = sel.css('p.short').extract_first()
    long_blurb = sel.css('p.long').extract_first()
    print("\nword_text: {}".format(word_text))
    print("\nshort_blurb: {}".format(short_blurb))
    print("\nlong_blurb: {}".format(long_blurb))
    
    word = self.dbi.get_or_create(self.ssn, self.dbi.Word, word = word_text)
    word.short_blurb = short_blurb
    word.long_blurb = long_blurb

    for sense_div in sel.css('div.sense'):
      sense_def = sense_div.css('h3.definition::text').extract()[-1].strip()
      sense = self.dbi.get_or_create(self.ssn, self.dbi.Sense, sense = sense_def)
      sense.word_collection.append(word)

      self.ssn.commit()

      print("\n  sense: {}".format(sense_def))

      for instance in sense_div.css('dl.instances'):
        kind_text = instance.css('dt::text').extract_first()
        if kind_text:
          # If kind_text is not set, then kind will changed from its last
          # value, which is what we want.
          kind = kind_text.lower()
        if kind[:-1] in ('synonyms', 'antonyms', 'types', 'type of'):
          print("    {}".format(kind))
          self.process_instance(instance, kind, word, sense)

    word.is_task_complete = True
    self.ssn.commit()

  def maybe_updatewords(self):
    yield from self.get_mainpage()
    yield from self.get_listspage()

    link_elements = self.drv.find_elements_by_css_selector('table > tbody > tr > td > a')
    # I can't use the original list of link elements for the iterations below,
    # because I'm switching pages, which makes the list stale.
    a_ct = len(link_elements)
    # So instead I iterate over the length of the list,
    print("entering loop...")
    for i in range(a_ct):
      # and on each iteration I refresh the list,
      self.waitget_elem_by_css('table > tbody > tr > td > a')
      link_elements = self.drv.find_elements_by_css_selector('table > tbody > tr > td > a')
      # and then get the ith link.
      a = link_elements[i]
      list_description = a.text.split('\n')[0]
      link = a.get_attribute('href')
      list_id = link.split('/')[-1]
      vocab_list = self.dbi.get_or_create(self.ssn, self.dbi.Vocab, id = list_id)
      print('maybe_updatewords: examining list "{}"...'.format(vocab_list))
      if vocab_list.description != list_description:
        vocab_list.description = list_description
        self.ssn.commit()
      
      a.click()
      yield get_boundedsleep(self.nav_kde, self.mnsleep_mu, self.mnsleep_sd)
      
      self.waitget_elem_by_css('.wordlist li')
      entries = self.drv.find_elements_by_css_selector('.wordlist li')
      entries_ct = len(entries)
      #for entry in entries:
      for j in range(entries_ct):
        self.waitget_elem_by_css('.wordlist li')
        entries = self.drv.find_elements_by_css_selector('.wordlist li')
        entry = entries[j]
        
        entry_a = entry.find_element_by_css_selector('a.word')
        word_text = entry_a.text
        freq = entry.get_attribute('freq')
        print('maybe_updatewords: processing word "{}"...'.format(word_text))
        word = self.dbi.get_or_create(self.ssn, self.dbi.Word, word = word_text)
        if word.is_task_complete:
          print("Word is already processed; skipping.")
        else:
          word.freq = freq
          vocab_list.word_collection.append(word)

          period_for_word = get_boundedsleep(
            self.study_kde, self.msleep_mu, self.msleep_sd
          )
          subperiod_to_word = get_boundedsleep(
            self.nav_kde, self.mnsleep_mu, self.mnsleep_sd
          )
          subperiod_from_word = get_boundedsleep(
            self.nav_kde, self.mnsleep_mu, self.mnsleep_sd
          )
          subperiod_for_word = period_for_word - (subperiod_to_word + subperiod_from_word)

          print("period for this word: {}".format(
            period_for_word
          ))
          print("subperiods for this word: {} + {} + {}".format(
            subperiod_to_word,
            subperiod_for_word,
            subperiod_from_word,
          ))

          entry_a.click()
          yield subperiod_to_word

          self.waitget_elem_by_css('.dynamictext')
          self.examine_word(drv.page_source)
          yield subperiod_for_word

          self.drv.back()
          yield subperiod_from_word

      print('maybe_updatewords: hooray, updated list!')
      vocab_list.is_task_complete = True
      self.ssn.commit()
      print('maybe_updatewords: yielding...')

      period = get_boundedsleep(self.study_kde, self.msleep_mu, self.msleep_sd)
      yield period

      print('maybe_updatewords: back...')
      self.drv.back()
      yield get_boundedsleep(self.nav_kde, self.mnsleep_mu, self.mnsleep_sd)
        


def do_all_the_things():
  ssn = get_session()
  svc, drv = get_webdriver()
  study_ds = get_ds()
  nav_ds = study_ds/6
  study_kde = get_kde(study_ds)
  nav_kde = get_kde(nav_ds)
  scraper = Scraper(ssn, dbi, drv, study_kde, nav_kde)
  schedule = get_hourly_schedule(None, n = 2)
  asyncio.ensure_future(work_async(scraper.maybe_updatelists(), schedule))


if __name__ == "__main__":
  do_all_the_things()
