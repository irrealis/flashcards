#!/usr/bin/env python3

from anki_connect_client import AnkiConnectClient
import markdown, pandas, pweave.themes, rtyaml

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


log = logging.getLogger('update_notes')
log.addHandler(logging.StreamHandler())


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




class NoteSender(object):
  def __init__(self, opts):
    self.setopts(opts)
    self.anki = AnkiConnectClient()
    self.pweb = MyPweb(
      source = "anon", doctype = 'md2html',
      informat = 'markdown', mimetype = 'text/markdown',
    )
    self.pweb.set_anki(self.anki)


  def setopts(self, opts):
    self.opts = opts


  def extract_defaults(self, data):
    rt_defs = data.get('defaults', dict())
    defaults = dict(
      deckName = rt_defs.get('deckName', self.opts.default_deckname),
      modelName = rt_defs.get('modelName', self.opts.default_modelname),
      annotationsField = rt_defs.get('annotationsField', self.opts.default_annfield),
      useMarkdown = rt_defs.get('useMarkdown', self.opts.default_md_proc),
      markdownStyle = rt_defs.get('markdownStyle', self.opts.default_md_style),
      markdownLineNums = rt_defs.get('markdownLineNums', self.opts.default_md_lineno),
      markdownTabLength = rt_defs.get('markdownTabLength', self.opts.default_md_tablen),
      useMarkdownMathExt = rt_defs.get('useMarkdownMathExt', self.opts.default_md_mathext),
      extraTags = rt_defs.get('extraTags', list()),
      fields = rt_defs.get('fields', dict()),
    )
    return defaults


  def extract_note(self, rtnote, defaults):
    # We want at least a bogus note ID of 0 to be present.
    if 'id' not in rtnote: rtnote['id'] = 0
    # We want a shallow copy of all round-trip data.
    note = dict(rtnote)
    # We also want the original round-trip data in case we need to change the YAML file.
    note['rtnote'] = rtnote
    # Below we may make changes to the shallow-copy data that we don't want reflected in the YAML file.
    note.setdefault('deckName', defaults['deckName'])
    note.setdefault('modelName', defaults['modelName'])
    note.setdefault('useMarkdown', defaults['useMarkdown'])
    note.setdefault('markdownStyle', defaults['markdownStyle'])
    note.setdefault('markdownLineNums', defaults['markdownLineNums'])
    note.setdefault('markdownTabLength', defaults['markdownTabLength'])
    note.setdefault('useMarkdownMathExt', defaults['useMarkdownMathExt'])
    note.setdefault('annotationsField', defaults['annotationsField'])

    # Tags and fields require special handling.
    # For tags we need to:
    # - Add any default extra tags.
    # - Convert to a comma-separated list. This permits querying notes by tags
    # using a comma-separated syntax in querynotes(...).
    tags = defaults['extraTags'].copy()
    tags.extend(note.get('tags', list()))
    note['tags'] = ',{},'.format(','.join(sorted(tags)))
    # For fields we want to use any defaults not specified in the note. So if
    # field 'Fubar' is in defaults, but not in the note, then we use the
    # default. But if the note has its own version of 'Fubar', then we use the
    # note's version.
    fields = dict(defaults['fields'])
    fields.update(note.get("fields", dict()))
    note['fields'] = fields

    # There are two pieces of data we may want to modify in the original file.
    # To avoid confusion, we remove shallow copies of these data, and will use
    # the round-trip versions instead. These data are:
    # - The note ID. If a note with that ID can't be found in Anki's flashcard
    #   deck, we assume the existing ID is bogus. We'll then create a new note,
    #   get its ID, and replace the bogus ID with new ID, and store the new ID
    #   in the YAML file.
    # - The annotations field. If we can find this note in Anki's flashcard
    #   deck, then we'll grab any annotations the user has made for that note,
    #   and store them in the YAML file. If we are instead creating a new note,
    #   we'll transfer any annotations from the YAML file to the new note.
    # del note['id']
    annotations_field = defaults['annotationsField']
    if annotations_field in note['fields']:
      del note['fields'][annotations_field]

    return note


  def query_notes(self, query, data):
    defaults = self.extract_defaults(data)
    notes = [self.extract_note(rtnote, defaults) for rtnote in data['notes']]
    notes_df = pandas.DataFrame(notes)
    if query: query_results = notes_df.query(query)
    else: query_results = notes_df
    return query_results, defaults


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


  def loadsend_file(self, filename):
    with rtyaml.edit(filename, default = {}) as data:
      query_results, defaults = self.query_notes(self.opts.query, data)
      if query_results.empty:
        log.warning("Query returned no results.")
      else:
        log.debug("query_results:\n %s", str(query_results))
      for i in query_results.index:
        rtnote = query_results.rtnote[i]
        note_id = str(rtnote['id'])
        deck = query_results.deckName[i]
        model = query_results.modelName[i]
        use_md = query_results.useMarkdown[i]
        md_sty = query_results.markdownStyle[i]
        md_lineno = query_results.markdownLineNums[i]
        md_tablen = query_results.markdownTabLength[i]
        md_mathext = query_results.useMarkdownMathExt[i]
        tags = query_results.tags[i].replace(',','\n').split()
        fields = query_results.fields[i]
        description = "{}:{}".format(note_id, fields)

        log.info("Processing note with ID: {}".format(note_id))
        # Check for note with given ID.
        # Get info for existing note.
        creating_new_note = True
        result = self.anki.notesInfo([note_id])
        if result.get("error", None) or not result['result'][0]:
          log.info("Can't find note with ID %s; a new note will be created.", note_id)
        else:
          creating_new_note = False

        if creating_new_note:
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
            prev_id, rtnote['id'] = rtnote['id'], note_id
            if prev_id:
              log.info("ID %s replaced with %s.", prev_id, note_id)
            else:
              log.warn("Failed to assign new note ID!")

        log.debug("Updating note...")
        # Assume provided ID is valid for existing note to be updated.
        # Convert each field from Markdown (if `use_md` is True).
        note_uid = uuid.uuid1()
        converted_fields = { k: self.format_text(
          str(v), use_md, md_sty, md_lineno, md_tablen, md_mathext,
          note_id = "%s-%s-%s" % (note_id, note_uid, field_no)
        ) for (field_no, (k, v)) in enumerate(fields.items()) }

        # Update converted note fields...
        result = self.anki.updateNoteFields(note_id, converted_fields)
        if result.get("error", None):
          log.warning("Can't update note: %s", description)
          continue


        result = self.anki.notesInfo([note_id])

        # Update note tags...
        ## First get existing note tags.
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


  def loadsend_files(self, filenames):
    for input_filename in filenames:
      self.loadsend_file(input_filename)

  def loadsend(self):
    return self.loadsend_files(self.opts.input)


def getopts():
  '''Parse command-line arguments.'''
  defs = dict(
    def_deckname = 'Default',
    def_modelname = 'BasicMathJax',
    def_annfield = 'Annotations',
    def_md_proc = 'Python-Markdown',
    def_md_sty = 'tango',
    def_md_tablen = 4,
    def_md_lineno = False,
    def_md_mathext = True,
  )

  parser = argparse.ArgumentParser(
    description = "Update Anki flashcards parsed from YAML."
  )
  parser.add_argument(
    "-q", "--query",
    help = "Query for filtering notes"
  )
  parser.add_argument(
    "-d", "--debug",
    help = "Enable debugging output and routines",
    action = 'store_true',
    default = False,
  )
  parser.add_argument(
    "input",
    help = "YAML file(s) with flashcard content",
    nargs = '+',
  )
  parser.add_argument(
    "--default-deckname",
    help = "Default deck name to use in Anki (default: {def_deckname})".format(**defs),
    default = defs['def_deckname'],
  )
  parser.add_argument(
    "--default-modelname",
    help = "Default model name to use in Anki (default: {def_modelname})".format(**defs),
    default = defs['def_modelname'],
  )
  parser.add_argument(
    "--default-annfield",
    help = "Default note field to use for annotations in Anki (default: {def_annfield})".format(**defs),
    default = defs['def_annfield'],
  )
  parser.add_argument(
    "--default-md-proc",
    help = "Default Markdown processor (default: {def_md_proc})".format(**defs),
    default = defs['def_md_proc'],
  )
  parser.add_argument(
    "--default-md-style",
    help = "Default Markdown style (default: {def_md_sty})".format(**defs),
    default = defs['def_md_sty'],
  )
  parser.add_argument(
    "--default-md-tablen",
    help = "Default Markdown tab length (default: {def_md_tablen})".format(**defs),
    type = int,
    default = defs['def_md_tablen'],
  )

  md_lineno_parser = parser.add_mutually_exclusive_group(required = False)
  md_lineno_parser.add_argument(
    "--default-md-lineno",
    help = "Enable default Markdown line numbering{}".format(' (default)' if defs['def_md_lineno'] else ''),
    dest = 'default_md_lineno',
    action = 'store_true',
  )
  md_lineno_parser.add_argument(
    "--no-default-md-lineno",
    help = "Disable default Markdown line numbering{}".format('' if defs['def_md_lineno'] else ' (default)'),
    dest = 'default_md_lineno',
    action = 'store_false',
  )
  parser.set_defaults(default_md_lineno = defs['def_md_lineno'])

  md_mathext_parser = parser.add_mutually_exclusive_group(required = False)
  md_mathext_parser.add_argument(
    "--default-md-mathext",
    help = "Enable default Markdown math extension{}".format(' (default)' if defs['def_md_mathext'] else ''),
    dest = 'default_md_mathext',
    action = 'store_true',
  )
  md_mathext_parser.add_argument(
    "--no-default-md-mathext",
    help = "Disable default Markdown math extension{}".format('' if defs['def_md_mathext'] else ' (default)'),
    dest = 'default_md_mathext',
    action = 'store_false',
  )
  parser.set_defaults(default_md_mathext = defs['def_md_mathext'])

  return parser.parse_args()


def main():
  opts = getopts()

  if opts.debug: log.setLevel('DEBUG')
  else: log.setLevel('INFO')
  log.debug("\ncmdline args:")
  for k, v in vars(opts).items():
    log.debug("  %s: %s", k, v)

  # Load and parse flashcard data from input YAML file.
  sender = NoteSender(opts)
  sender.loadsend()
  log.info("\nDone.\n")


if __name__ == "__main__": main()
