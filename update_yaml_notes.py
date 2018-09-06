#!/usr/bin/env python3

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

import argparse, logging

log = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler()
log.addHandler(log_hdlr)


def report_anki_error(anki_result, message, *extra_args):
  log.warning(message, *extra_args)
  log.warning("\nAnkiConnect error description:\n %s", anki_result["error"])


def format_text(
  text,
  useMarkdown,
  markdownStyle,
  markdownLineNums,
  markdownTabLength,
):
  if useMarkdown:
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
    log.info("\nSending file '{}' to Anki...\n".format(filename))
    nodes = yaml.compose(yaml_input_file)
    data = yaml.load(yaml.serialize(nodes))
    defaults = data.get('defaults', None)
    log.debug("defaults: {}".format(defaults))

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

    # For each note_node in notes_node:
    new_notes_were_created = False
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
        log.debug("Updating existing note...")
        # Update using ID
        note_id = note['id']

        response, result = connection.send_as_json(
          action = "notesInfo",
          params = dict(notes = [note_id])
        )
        if result.get("error", None):
          report_anki_error(result, "Can't get tags for note: %s", note)
        current_tags = " ".join(result['result'][0]['tags'])

        response, result = connection.send_as_json(
          action = "removeTags",
          params = dict(notes = [note_id], tags = current_tags)
        )
        if result.get("error", None):
          report_anki_error(result, "Can't remove tags for note: %s", note)

        response, result = connection.send_as_json(
          action = "addTags",
          params = dict(notes = [note_id], tags = " ".join(tags))
        )
        if result.get("error", None):
          report_anki_error(result, "Can't add tags for note: %s", note)

        # Update note fields...
        params = dict(note = dict(id = note_id, fields = fields))
        log.debug("params: {}".format(params))
        response, result = connection.send_as_json(
          action = "updateNoteFields",
          params = params,
        )
        if result.get("error", None):
          report_anki_error(result, "Can't update note: %s", note)

      else:
        log.debug("Creating new note...")
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
          report_anki_error(result, "Can't create note: %s", note)
        else:
          # Add ID to note_node
          note_id = result['result']
          note_node.value.insert(0, (
            yaml.ScalarNode(tag='tag:yaml.org,2002:str', value='id'),
            yaml.ScalarNode(tag='tag:yaml.org,2002:int', value=str(note_id)),
          ))
          new_notes_were_created = True

  if new_notes_were_created:
    # Write updated nodes to disk.
    with open(filename, mode = 'w') as yaml_output_file:
      log.info("\nUpdating file '{}' with new note IDs...".format(filename))
      yaml_output_file.write(yaml.serialize(nodes))


def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Update Anki flashcards parsed from YAML."
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
  opts = parse_cmdline()
  log.info("cmdline args:", opts)
  if opts.debug: log.setLevel('DEBUG')
  else: log.setLevel('INFO')

  # Load and parse flashcard data from input YAML file.
  for input_filename in opts.input:
    load_and_send_flashcards(input_filename)
  log.info("\nDone.\n")


if __name__ == "__main__": main()
