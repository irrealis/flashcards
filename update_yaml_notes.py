from anki_connect_client import AnkiConnectClient

import yaml
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
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.tables import TableExtension

import argparse


def load_and_send_flashcards(yaml_input_file):
  nodes = yaml.compose(yaml_input_file)
  data = yaml.load(yaml.serialize(nodes))
  defaults = data.get('defaults', None)
  print("defaults: {}".format(defaults))


def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Send Anki flashcards parsed from YAML."
  )
  parser.add_argument(
    "-d", "--debug",
    action = 'store_true',
    default = False,
    help = "Enable debugging output and routines"
  )
  parser.add_argument(
    "input",
    nargs = '+',
    help = "YAML file(s) with flashcard content"
  )
  return parser.parse_args()

def main():
  cmdline_args = parse_cmdline()
  print("cmdline_args:", cmdline_args)

  # Load and parse flashcard data from input YAML file.
  for input_filename in cmdline_args.input:
    with open(input_filename) as yaml_input_file:
      print("\nSending file '{}' to Anki...".format(input_filename))
      load_and_send_flashcards(yaml_input_file)
  print("\nDone.\n")


if __name__ == "__main__":
  main()
