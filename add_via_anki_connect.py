#!/usr/bin/env python3

import yaml, pypandoc
import markdown
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.smart_strong import SmartEmphasisExtension
from markdown.extensions.tables import TableExtension

import argparse, http.client, json


class AnkiConnectException(Exception):
  pass


class AnkiConnectClient(object):
  server_version = 6

  def __init__(self, hostname = None, port = None):
    self.connection = None
    self.connect(hostname, port)

  def __del__(self):
    self.close()

  def connect(self, hostname = None, port = None):
    '''Open HTTP connection to AnkiConnect.'''
    self.close()
    if hostname is None: hostname = '127.0.0.1'
    if port is None: port = 8765
    self.hostname = hostname
    self.port = port
    self.connection = http.client.HTTPConnection(self.hostname, self.port)

  def close(self):
    '''Close HTTP connection to AnkiConnect.'''
    if self.connection: self.connection.close()

  def send_raw(self, data):
    '''Send raw data to AnkiConnect.'''
    self.close()
    self.connection.request("POST", "", data)
    response = self.connection.getresponse()
    return response

  def send_as_json(self, data = None, version = None, **d):
    '''
    Convert data to JSON, then send to AnkiConnect.

    Returns both HTTP response and any data from AnkiConnect.
    '''
    # To simplify calling `send_as_json`, named parameters can be used in
    # place of a data dict.
    if data is None: data = d

    # If AnkiConnect version isn't supplied, use this class's default.
    if version is None: version = AnkiConnectClient.server_version
    data.setdefault("version", version)
    json_data = json.dumps(data)
    http_response = self.send_raw(json_data)
    json_result_data = http_response.read()
    result_data = json.loads(json_result_data)
    return http_response, result_data

  def send(self, data = None, version = None, **d):
    '''
    Simplified send of data to AnkiConnect in JSON format.

    Returns any data from AnkiConnect.
    '''
    http_response, result_data = self.send_as_json(data, version, **d)

    # Propagate error if indicated by non-None value in "error" field.
    # Note: AnkiConnect doesn't use this field for certain errors.
    if result_data["error"] is not None:
      msg = "error: {}, http status: {}, http reason: {}".format(
        result_data["error"],
        http_response.status,
        http_response.reason,
      )
      raise AnkiConnectException(msg)

    # If no error indicated in "error" field, return data from AnkiConnect.
    return result_data


def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Send Anki flashcards parsed from YAML."
  )
  parser.add_argument(
    "input",
    nargs = '+',
    help = "YAML file(s) with flashcard content"
  )
  return parser.parse_args()


def format_text(
  text,
  useMarkdown,
  markdownStyle,
  markdownLineNums,
  markdownTabLength,
):
  if useMarkdown:
    #html_ish = pypandoc.convert_text(
    #  text,
    #  'html',
    #  'markdown_github+backtick_code_blocks+fenced_code_attributes'
    #)
    html_ish = markdown.markdown(text, output_format="xhtml1",
      extensions=[
        SmartEmphasisExtension(),
        FencedCodeExtension(),
        FootnoteExtension(),
        AttrListExtension(),
        DefListExtension(),
        TableExtension(),
        AbbrExtension(),
        Nl2BrExtension(),
        CodeHiliteExtension(
          noclasses = True,
          pygments_style = markdownStyle,
          linenums = markdownLineNums
        ),
        SaneListExtension()
      ],
      lazy_ol = False,
      tab_length = markdownTabLength,
    )
  else:
    # Preserve whitespace.
    html_ish = text.replace('\n', '<br>').replace(' ', '&nbsp;')
  return html_ish


def data_to_flashcards_params(data):
  '''Convert data to format accepted by AnkiConnect.'''
  tags = data["tags"]
  deckName = data["deckName"]
  modelName = data["modelName"]
  useMarkdown = data.get("useMarkdown", True)
  markdownStyle = data.get("markdownStyle", "tango")
  markdownLineNums = data.get("markdownLineNums", False)
  markdownTabLength = data.get("markdownTabLength", 4)
  params = dict(
    notes = [
      dict(
        tags = tags,
        deckName = deckName,
        modelName = modelName,
        fields = {
          k: format_text(
            v,
            useMarkdown,
            markdownStyle,
            markdownLineNums,
            markdownTabLength,
          )
          for (k, v) in note.items()
        }
      )
      for note in data["notes"]
    ]
  )
  return params


def anki_connect_version(connection):
  return connection.send(action = "version")


def send_flashcards_to_anki(connection, params):
  return connection.send_as_json(
    action = "addNotes",
    params = params
  )


def load_and_send_flashcards_to_anki(yaml_input_file):
  flashcard_data = yaml.load(yaml_input_file)
  flashcard_params = data_to_flashcards_params(flashcard_data)

  # Send data to AnkiConnect with request to create flashcards.
  connection = AnkiConnectClient()
  http_response, result_data = send_flashcards_to_anki(connection, flashcard_params)

  # Report any errors.
  notes = flashcard_data["notes"]
  results = result_data["result"]
  for note, result in zip(notes, results):
    if result is None:
      print("\n*** Couldn't add note: {}".format(note))

  if result_data["error"]:
    print("\n--- HTTP response:\n{} {}\n--- AnkiConnect error description:\n{}".format(
      http_response.status,
      http_response.reason,
      result_data["error"]
    ))


def main():
  cmdline_args = parse_cmdline()

  # Load and parse flashcard data from input YAML file.
  for input_filename in cmdline_args.input:
    with open(input_filename) as yaml_input_file:
      print("\nSending file '{}' to Anki...".format(input_filename))
      load_and_send_flashcards_to_anki(yaml_input_file)
  print("\nDone.\n")

if __name__ == "__main__":
  main()
