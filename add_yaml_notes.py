#!/usr/bin/env python3

from anki_connect_client import AnkiConnectClient

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

import argparse

def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Send Anki flashcards parsed from YAML."
  )
  parser.add_argument(
    "-d", "--debug",
    action = 'store_true',
    default = False,
    help = "Use slower routines for debugging"
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
    noclasses = markdownStyle != 'default'
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
          noclasses = noclasses,
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
            str(v),
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


def load_and_send_individual_flashcards_to_anki(yaml_input_file):
  flashcard_data = yaml.load(yaml_input_file)
  flashcard_params = data_to_flashcards_params(flashcard_data)

  connection = AnkiConnectClient()

  for note in flashcard_params["notes"]:
    http_response, result_data = connection.send_as_json(
      action = "addNote",
      params = dict(
        note = note
      )
    )
    if result_data.get("error", None):
      print("\n*** Couldn't add note: {}\n--- AnkiConnect error description:\n{}\n--- HTTP response:\n{} {}".format(
        note,
        result_data["error"],
        http_response.status,
        http_response.reason,
      ))

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
    print("\n--- AnkiConnect error description:\n{}\n--- HTTP response:\n{} {}\n".format(
      result_data["error"],
      http_response.status,
      http_response.reason,
    ))


def main():
  cmdline_args = parse_cmdline()
  print("cmdline_args:", cmdline_args)

  # Load and parse flashcard data from input YAML file.
  for input_filename in cmdline_args.input:
    with open(input_filename) as yaml_input_file:
      print("\nSending file '{}' to Anki...".format(input_filename))
      if cmdline_args.debug:
        load_and_send_individual_flashcards_to_anki(yaml_input_file)
      else:
        load_and_send_flashcards_to_anki(yaml_input_file)
  print("\nDone.\n")

if __name__ == "__main__":
  main()
