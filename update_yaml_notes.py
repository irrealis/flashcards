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


def format_text(
  text,
  useMarkdown,
  markdownStyle,
  markdownLineNums,
  markdownTabLength,
):
  if useMarkdown:
    # html_ish = pypandoc.convert_text(
    #   text,
    #   'html',
    #   'markdown_github+backtick_code_blocks+fenced_code_attributes'
    # )
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
        SaneListExtension(),
        SmartyExtension()
      ],
      lazy_ol = False,
      tab_length = markdownTabLength,
    )
  else:
    # Preserve whitespace.
    html_ish = text.replace('\n', '<br>').replace(' ', '&nbsp;')
  return html_ish


def load_and_send_flashcards(filename):
  with open(filename) as yaml_input_file:
    nodes = yaml.compose(yaml_input_file)
    data = yaml.load(yaml.serialize(nodes))
    defaults = data.get('defaults', None)
    print("defaults: {}".format(defaults))

    def_tags = defaults.get("tags", list())
    def_deckName = defaults.get("deckName", "Default")
    def_modelName = defaults.get("modelName", "BasicMathJax")
    def_fields = defaults.get("fields", dict())
    def_useMarkdown = defaults.get("useMarkdown", True)
    def_markdownStyle = defaults.get("markdownStyle", "tango")
    def_markdownLineNums = defaults.get("markdownLineNums", False)
    def_markdownTabLength = defaults.get("markdownTabLength", 4)

    # Extract notes_node
    top_map = {k.value:v.value for k,v in nodes.value}
    note_nodes = top_map['notes']

    connection = AnkiConnectClient()

    new_notes_were_created = False

    # For each note_node in notes_node:
    for note_node in note_nodes:
      # Convert to note_dict
      note = yaml.load(yaml.serialize(note_node))

      tags = note.get('tags', def_tags)
      deckName = note.get('deckName', def_deckName)
      modelName = note.get('modelName', def_modelName)

      # Set note's fields to defaults, if not already set.
      fields = dict(def_fields)
      fields.update(note.get("fields", dict()))
      fields = {
        # Convert each field from Markdown (if `useMarkdown` is True).
        k: format_text(
          str(v),
          note.get('useMarkdown', def_useMarkdown),
          note.get('markdownStyle', def_markdownStyle),
          note.get('markdownLineNums', def_markdownLineNums),
          note.get('markdownTabLength', def_markdownTabLength),
        )
        for (k, v) in fields.items()
      }

      if 'id' in note:
        print("Would update existing note...")
      else:
        print("Creating new note...")
        # Create, obtaining returned ID
        response, result = connection.send_as_json(
          action = "addNote",
          params = dict(
            note = dict(
              deckName = deckName,
              modelName = modelName,
              fields = fields,
              tags = tags,
            )
          )
        )

        if result.get("error", None):
          print("\n*** Couldn't remove existing tags for note: {}".format(
            note,
          ))
          print("--- AnkiConnect error description:\n{}".format(
            result["error"],
          ))
          print("--- HTTP response:\n{} {}".format(
            response.status,
            response.reason,
          ))
        else:
          # Add ID to note_node
          note_id = result['result']
          note_node.value.insert(
            0,
            (
              yaml.ScalarNode(tag='tag:yaml.org,2002:str', value='id'),
              yaml.ScalarNode(tag='tag:yaml.org,2002:int', value=str(note_id)),
            )
          )
          new_notes_were_created = True

  if new_notes_were_created:
    # Write updated nodes to disk.
    with open(filename, mode = 'w') as yaml_output_file:
      print("\nUpdating file '{}' with new note IDs...".format(filename))
      yaml_output_file.write(yaml.serialize(nodes))


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
