#!/usr/bin/env python3

import markdown, pandas, pweave.themes, yaml
from anki_connect_client import AnkiConnectClient
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
from pweave.formatters.publish import PwebHTMLFormatter
from pweave.formatters.markdownmath import MathExtension
from pweave.mimetypes import MimeTypes
from pweave.pweb import Pweb
from pweave.readers import PwebReaders
from pygments.formatters import HtmlFormatter

import argparse, base64, logging, os, time, uuid


log = logging.getLogger('update_yaml_notes_pweave')
log_hdlr = logging.StreamHandler()
log.addHandler(log_hdlr)


def extract_note(note_node, defaults):
  note = yaml.load(yaml.serialize(note_node))

  if 'id' not in note:
    note['id'] = 0
    # We want to update the YAML file with a new note ID, but modifying a YAML
    # file is complicated. One way to do it is via a lower-level interface. Here
    # we use the nodes representation, which we modify directly. The nodes
    # representation can then be converted into a YAML file that fairly
    # faithfully resembles the original, but with the newly added note ID.
    note_node.value.insert(0, (
      yaml.ScalarNode(tag='tag:yaml.org,2002:str', value='id'),
      yaml.ScalarNode(tag='tag:yaml.org,2002:int', value=str(note['id'])),
    ))

  note.setdefault('deckName', defaults.get("deckName", "Default"))
  note.setdefault('modelName', defaults.get("modelName", "BasicMathJax"))
  note.setdefault('useMarkdown', defaults.get("useMarkdown", True))
  note.setdefault('markdownStyle', defaults.get("markdownStyle", "tango"))
  note.setdefault('markdownLineNums', defaults.get("markdownLineNums", False))
  note.setdefault('markdownTabLength', defaults.get("markdownTabLength", 4))
  note.setdefault('useMarkdownMathExt', defaults.get("useMarkdownMathExt", True))

  tags = defaults.get("extraTags", list()).copy()
  tags.extend(note.get('tags', list()))
  note['tags'] = ',{},'.format(','.join(sorted(tags)))

  fields = dict(defaults.get("fields", dict()))
  fields.update(note.get("fields", dict()))
  note['fields'] = fields

  note['node'] = note_node
  return note


def query_note_nodes(nodes, opts):
  data = yaml.load(yaml.serialize(nodes))
  defaults = data.get('defaults', None)
  top_map = {k.value:v.value for k,v in nodes.value}
  note_nodes = top_map['notes']
  notes = [extract_note(note_node, defaults) for note_node in note_nodes]
  notes_df = pandas.DataFrame(notes)
  if opts.query:
    query_results = notes_df.query(opts.query)
  else:
    query_results = notes_df
  return query_results, defaults, data, note_nodes, notes


def parse_markdown(text, noclasses, style, line_nums, tab_len, mathext):
  extensions = []
  if mathext: extensions.append(MathExtension())
  extensions.extend([
    SmartEmphasisExtension(), FencedCodeExtension(),
    FootnoteExtension(), AttrListExtension(), DefListExtension(),
    TableExtension(), AbbrExtension(), Nl2BrExtension(),
    CodeHiliteExtension(
      noclasses = noclasses, pygments_style = style, linenums = line_nums,
    ),
    SaneListExtension(), SmartyExtension()
  ])
  return markdown.markdown(
    text,
    output_format="xhtml1",
    extensions = extensions,
    lazy_ol = False,
    tab_length = tab_len,
  )


htmltemplate = {}
htmltemplate["header"] = \
"""
<div class ="container">
  <div class = "row">
    <div class = "col-md-12 twelve columns">
"""
htmltemplate["footer"]="""
      </div>
  </div>
</div>
"""


class MyPwebMDtoHTMLFormatter(PwebHTMLFormatter):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.set_anki()
    self.set_markdown_opts()
    self.mimetypes = ["text/html", "text/markdown", "application/javascript"]
    theme_css = ""
    try:
      theme_css += getattr(pweave.themes, self.theme)
    except:
      log.warn("Can't find requested theme. Using Skeleton")
      theme_css += getattr(pweave.themes, "skeleton")
    self.header = (htmltemplate["header"] %
            {"pygments_css"  : HtmlFormatter().get_style_defs(),
            "theme_css" : theme_css})
    self.footer = (htmltemplate["footer"] %
                   {"source": self.source, "version": pweave.__version__,
                    "time": time.strftime("%d-%m-%Y", time.localtime())})

  def set_source(self, source = 'anon'):
    self.source = source

  def set_anki(self, anki = None):
    if anki is None:
      anki = AnkiConnectClient()
    self.anki = anki

  def set_markdown_opts(
    self,
    style = "tango",
    line_nums = True,
    tab_len = 2,
    mathext = True,
  ):
    self.md_sty = style
    self.md_lineno = line_nums
    self.md_tablen = tab_len
    self.md_mathext = mathext

  def parsetitle(self, chunk):
    """Parse titleblock from first doc chunk, like Pandoc"""
    lines = chunk['content'].splitlines()
    if len(lines) > 3:
      if lines[0].startswith("%"):
          lines[0] = '<H1 class = "title">%s</H1>' % (lines[0].replace("%", "", ))
          if lines[1].startswith("%"):
            lines[1] = '<strong>Author:</strong> %s <BR/>' % (lines[1].replace("%", "", ))
          if lines[2].startswith("%"):
            lines[2] = '<strong>Date:</strong> %s <BR/>' % (lines[2].replace("%", "", ))
    chunk['content'] = "\n".join(lines)
    return chunk

  def format_docchunk(self, chunk):
    if 'number' in chunk and chunk['number'] == 1:
      chunk = self.parsetitle(chunk)
    noclasses = self.md_sty != "default"
    chunk["content"] = parse_markdown(
      chunk["content"],
      noclasses,
      self.md_sty,
      self.md_lineno,
      self.md_tablen,
      self.md_mathext,
    )
    return chunk['content']

  def formatfigure(self, chunk):
    result = ""
    figstring = ""

    for fig in chunk['figure']:
      fh = open(os.path.join(self.wd, fig), "rb")
      bfig = fh.read()
      fh.close()
      fig_base64 = base64.b64encode(bfig).decode("utf-8")
      fig_basename = os.path.basename(fig)
      figstring += ('<img src="%s" width="%s"/>\n' % (fig_basename, chunk['width']))

      log.info("Storing new media: {}".format(fig_basename))
      anki_result = self.anki.storeMediaFile(fig_basename, fig_base64)
      if anki_result.get("error", None):
        log.warning("Can't store media file: %s", fig_basename)

    # Figure environment
    if chunk['caption']:
      # Write labels as data-attribute for javascript etc.
      if chunk['name']:
        labelstring = 'data-label = "fig:%s"' % chunk["name"]
      else:
        labelstring = ""

      result += ("<figure>\n" \
                 "%s"
                 "<figcaption %s>%s</figcaption>\n</figure>" % (figstring, labelstring, chunk['caption']))

    else:
      result += figstring
    return result


class MyPweb(Pweb):
  def __init__(self,
    source = None, doctype = None, *, informat = None, kernel = "python3",
    output = None, figdir = 'figures', mimetype = None
  ):
    self.source = source
    self.figdir = figdir
    self.doctype = doctype
    self.sink = None
    self.kernel = None
    self.language = None

    if mimetype:
      self.mimetype = MimeTypes.get_mimetype(mimetype)
    else:
      self.mimetype = MimeTypes.guess_mimetype(self.source)

    if self.source:
      name, file_ext = os.path.splitext(self.source)
      self.file_ext = file_ext.lower()
    else:
      self.file_ext = None

    self.output = output
    self.setkernel(kernel)
    self._setwd()

    #Init variables not set using the constructor
    #: Use documentation mode
    self.documentationmode = False
    self.parsed = None
    self.executed = None
    self.formatted = None
    self.reader = None
    self.theme = "skeleton"
    self.formatter = MyPwebMDtoHTMLFormatter(
      [], kernel = self.kernel, language = self.language,
      mimetype = self.mimetype.type, source = self.source, theme = self.theme,
      figdir = self.figdir, wd = self.wd,
    )
    self.set_anki()
    self.set_markdown_opts()

  def set_anki(self, anki = None):
    self.formatter.set_anki(anki)

  def set_markdown_opts(
    self,
    style = "tango",
    line_nums = True,
    tab_len = 2,
    mathext = True
  ):
    self.formatter.set_markdown_opts(style, line_nums, tab_len, mathext)

  def read(self, string=None, basename="string_input", reader = None):
    if reader is None:
      Reader = PwebReaders.guess_reader(self.source)
    elif isinstance(reader, str):
      Reader = PwebReaders.get_reader(reader)
    else:
      Reader = reader

    if string:
      self.reader = Reader(string=string)
      self.source = basename # non-trivial implications possible
      self.formatter.set_source(self.source)
    else:
      self.reader = Reader(file=self.source)

    self.reader.parse()
    self.parsed = self.reader.getparsed()



class FlashcardSender(object):
  def __init__(self):
    self.anki = AnkiConnectClient()
    self.pweb = MyPweb(
      source = "anon", doctype = 'md2html',
      informat = 'markdown', mimetype = 'text/markdown',
    )
    self.pweb.set_anki(self.anki)

  def format_text(
    self,
    text,
    use_md,
    md_sty,
    md_lineno,
    md_tablen,
    md_mathext,
    note_id = "anon",
  ):
    noclasses = md_sty != 'default'
    self.pweb.set_markdown_opts(md_sty, md_lineno, md_tablen, md_mathext)
    if str(use_md).lower() == 'pweave':
      self.pweb.read(string = text, basename = str(note_id), reader = 'markdown')
      self.pweb.run()
      self.pweb.format()
      html_ish = self.pweb.formatted
    elif use_md:
      body = parse_markdown(
        text,
        noclasses,
        md_sty,
        md_lineno,
        md_tablen,
        md_mathext,
      )
      html_ish = "{}\n{}\n{}".format(
        self.pweb.formatter.header, body, self.pweb.formatter.footer,
      )
    else:
      html_ish = text.replace('\n', '<br>').replace(' ', '&nbsp;')
    return html_ish

  def load_and_send_flashcards(self, filename, opts):
    with open(filename) as yaml_input_file:
      log.info("\nSending file '{}' to Anki...\n".format(filename))
      new_notes_were_created = False
      # The reason for the lower-level nodes representation of the YAML file is
      # that it can be used to make a modified version of the original YAML
      # file. We do this in two sections of code. In both cases, we add new note
      # IDs to the YAML file.
      nodes = yaml.compose(yaml_input_file)
      query_results, defaults, data, note_nodes, notes = query_note_nodes(nodes, opts)
      if query_results.empty:
        log.warning("Query returned no results.")
      else:
        log.debug("query_results:\n %s", str(query_results))

      # For each note_node in notes_node that matches query:
      for i in query_results.index:
        note_id = str(query_results.id[i])
        deck = query_results.deckName[i]
        model = query_results.modelName[i]
        use_md = query_results.useMarkdown[i]
        md_sty = query_results.markdownStyle[i]
        md_lineno = query_results.markdownLineNums[i]
        md_tablen = query_results.markdownTabLength[i]
        md_mathext = query_results.useMarkdownMathExt[i]
        tags = query_results.tags[i].replace(',','\n').split()
        fields = query_results.fields[i]
        note_node = query_results.node[i]
        description = "{}:{}".format(note_id, fields)

        log.info("Processing note with ID: {}".format(note_id))
        # Check for note with given ID.
        # Get info for existing note.
        should_create_new_note = True
        must_replace_existing_note_id = False
        result = self.anki.notesInfo([note_id])
        if result.get("error", None) or not result['result'][0]:
          log.info("Can't find note with ID %s; a new note will be created.", note_id)
          must_replace_existing_note_id = True
        else:
          should_create_new_note = False

        if should_create_new_note:
          # No provided ID; assume new note should be created.
          log.debug("Creating new note...")
          temporary_fields = { k: self.format_text(
            str(v), False, md_sty, md_lineno, md_tablen, md_mathext,
          ) for (k, v) in fields.items() }

          # Create, obtaining returned ID
          result = self.anki.addNote(deck, model, temporary_fields, tags)
          if result.get("error", None):
            log.warning("Can't create note: %s", description)
          else:
            # Add ID to note_node
            note_id = result['result']
            if must_replace_existing_note_id:
              prev_id = None
              for k,v in note_node.value:
                if k.value == 'id':
                  prev_id, v.value = v.value, str(note_id)
              if prev_id:
                log.info("ID %s replaced with %s.", prev_id, note_id)
              else:
                log.warn("Failed to assign new note ID!")
            else:
              # We want to update the YAML file with a new note ID, but
              # modifying a YAML file is complicated. One way to do it is via a
              # lower-level interface. Here we use the nodes representation,
              # which we modify directly. The nodes representation can then be
              # converted into a YAML file that fairly faithfully resembles the
              # original, but with the newly added note ID.
              note_node.value.insert(0, (
                yaml.ScalarNode(tag='tag:yaml.org,2002:str', value='id'),
                yaml.ScalarNode(tag='tag:yaml.org,2002:int', value=str(note_id)),
              ))
            new_notes_were_created = True

        log.debug("Updating existing note...")
        # Assume provided ID is valid for existing note to be updated.
        # Convert each field from Markdown (if `use_md` is True).
        note_uid = uuid.uuid1()
        converted_fields = { k: self.format_text(
          str(v), use_md, md_sty, md_lineno, md_tablen, md_mathext,
          note_id = "%s-%s" % (note_id, note_uid)
        ) for (k, v) in fields.items() }

        # Update converted note fields...
        result = self.anki.updateNoteFields(note_id, converted_fields)
        if result.get("error", None):
          log.warning("Can't update note: %s", description)
          continue

        # Update note tags...
        ## First get existing note tags.
        result = self.anki.notesInfo([note_id])
        if result.get("error", None):
          log.warning("Can't get tags for note: %s", description)
          continue

        current_tags = sorted(result['result'][0]['tags'])
        if current_tags != tags:
          ## Remove existing note tags.
          result = self.anki.removeTags([note_id], " ".join(current_tags))
          if result.get("error", None):
            log.warning("Can't remove tags for note: %s", description)
          ## Add new note tags.
          result = self.anki.addTags([note_id], " ".join(tags))
          if result.get("error", None):
            log.warning("Can't add tags for note: %s", description)

    if new_notes_were_created:
      # If any new notes were created, their IDs must be added to YAML file.
      with open(filename, mode = 'w') as yaml_output_file:
        log.info("\nUpdating file '{}' with new note IDs...".format(filename))
        yaml_output_file.write(yaml.serialize(nodes))

  def load_and_send(self, opts):
    for input_filename in opts.input:
      self.load_and_send_flashcards(input_filename, opts)



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
    "-q", "--query",
    help = "Query for filtering notes"
  )
  parser.add_argument(
    "input",
    nargs = '+',
    help = "YAML file(s) with flashcard content"
  )
  return parser.parse_args()


def main():
  opts = parse_cmdline()

  if opts.debug: log.setLevel('DEBUG')
  else: log.setLevel('INFO')
  log.info("\ncmdline args:")
  for k, v in vars(opts).items():
    log.info("  %s: %s", k, v)

  # Load and parse flashcard data from input YAML file.
  flashcard_sender = FlashcardSender()
  flashcard_sender.load_and_send(opts)
  log.info("\nDone.\n")


if __name__ == "__main__": main()

#p*pk7!Iad9Yf1zM
#gG4R%viA!D&I5Px

# Wordnik API key:
#1bac5657ae5f32cc8900602fc16003760353ab07aa51b6ffe
