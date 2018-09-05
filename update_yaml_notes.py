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


def load_and_send_flashcards(filename):
  with open(filename) as yaml_input_file:
    nodes = yaml.compose(yaml_input_file)
    data = yaml.load(yaml.serialize(nodes))
    defaults = data.get('defaults', None)
    print("defaults: {}".format(defaults))

    # Extract notes_node
    top_map = {k.value:v.value for k,v in nodes.value}
    note_nodes = top_map['notes']

    connection = AnkiConnectClient()

    # For each note_node in notes_node:
    for note_node in note_nodes:
      # Convert to note_dict
      note = yaml.load(yaml.serialize(note_node))
      print("note: {}".format(note))



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
    load_and_send_flashcards(input_filename)
  print("\nDone.\n")


if __name__ == "__main__":
  main()
