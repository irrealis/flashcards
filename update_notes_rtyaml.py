#!/usr/bin/env python3

from anki_client import AnkiClient
import markdown, pandas, pweave.themes, rtyaml

from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.sane_lists import SaneListExtension
#from markdown.extensions.smart_strong import SmartEmphasisExtension
from markdown.extensions.smarty import SmartyExtension
from markdown.extensions.tables import TableExtension

from pweave.formatters.publish import PwebHTMLFormatter
from pweave.formatters.markdownmath import MathExtension
from pweave.mimetypes import MimeTypes
from pweave.pweb import Pweb
from pweave.readers import PwebReaders
from pygments.formatters import HtmlFormatter

import argparse, base64, logging, os, string, time, uuid, zlib


log = logging.getLogger('update_notes')
log.addHandler(logging.StreamHandler())
log.propagate = False


def parse_markdown(text, noclasses, style, line_nums, tab_len, mathext):
  extensions = []
  if mathext: extensions.append(MathExtension())
  extensions.extend([
    FencedCodeExtension(),
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
      anki = AnkiClient()
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
    self.anki = AnkiClient()
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
      skip = rt_defs.get('skip', False),
      deckName = rt_defs.get('deckName', self.opts.default_deckname),
      modelName = rt_defs.get('modelName', self.opts.default_modelname),
      useMarkdown = rt_defs.get('useMarkdown', self.opts.default_md_proc),
      markdownStyle = rt_defs.get('markdownStyle', self.opts.default_md_style),
      markdownLineNums = rt_defs.get('markdownLineNums', self.opts.default_md_lineno),
      markdownTabLength = rt_defs.get('markdownTabLength', self.opts.default_md_tablen),
      useMarkdownMathExt = rt_defs.get('useMarkdownMathExt', self.opts.default_md_mathext),
      annotationsField = rt_defs.get('annotationsField', self.opts.default_annfield),
      extraTags = rt_defs.get('extraTags', list()),
      fields = rt_defs.get('fields', dict()),
      media = rt_defs.get('media', list()),
    )
    return defaults


  def extract_note(self, rtnote, defaults):
    # We want at least a bogus note ID of 0 to be present.
    if 'id' not in rtnote: rtnote['id'] = 0
    # We want a shallow copy of all round-trip data.
    note = dict(rtnote)
    # We also want the original round-trip data in case we need to change the
    # YAML file.
    note['rtnote'] = rtnote

    # Below we may make changes to the shallow-copy data that we don't want
    # reflected in the YAML file.
    note.setdefault('skip', defaults['skip'])
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

    media = defaults['media'].copy()
    media.extend(note.get('media', list()))
    note['media'] = media

    annotations_field = defaults['annotationsField']
    if annotations_field in note['fields']:
      note['annotations'] = note['fields'][annotations_field]
    else:
      note['annotations'] = ''

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
    note_field_num = None,
    **d
  ):
    chunk_templ_vars = dict(d)

    if note_field_num is None: note_field_num = 0
    chunk_templ_vars['note_field_num'] = note_field_num

    subbed_text = string.Template(text).safe_substitute(chunk_templ_vars)
    noclasses = md_sty != 'default'
    self.pweb.set_markdown_opts(md_sty, md_lineno, md_tablen, md_mathext)
    if str(use_md).lower() == 'pweave':
      pweave_basename = string.Template("${note_id}-${note_uuid1}-${note_field_num}").safe_substitute(chunk_templ_vars)
      self.pweb.read(string = subbed_text, basename = pweave_basename, reader = 'markdown')
      self.pweb.run()
      self.pweb.format()
      html_ish = self.pweb.formatted
    elif use_md:
      body = parse_markdown(
        subbed_text,
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
      html_ish = subbed_text.replace('\n', '<br>').replace(' ', '&nbsp;')
    return html_ish


  def loadsend_file(self, filename):
    # Verify file can be opened.
    if not os.path.exists(filename): raise FileNotFoundError(filename)

    file_templ_vars = dict(
      file_name = os.path.abspath(filename),
      file_dir = os.path.abspath(os.path.dirname(filename)),
      file_uuid1 = uuid.uuid1(),
      work_dir = self.opts.workdir,
    )

    log.info('Processing "%s"...', filename)
    with rtyaml.edit(filename, default = {}) as data:
      query_results, defaults = self.query_notes(self.opts.query, data)
      if query_results.empty:
        log.warning("Query returned no results.")
      else:
        if self.opts.question:
          log.info("")
          log.info("Running in question mode.")
          log.info("Query results:\n %s", str(query_results))
          log.info("")
          log.info("Query result details below.")
          log.info("")
        else:
          if self.opts.annotations:
            log.info("")
            log.info("Running in annotations mode.")
            log.info("")
          log.debug("Query results:\n %s", str(query_results))

      annotations_field = defaults['annotationsField']
      for i in query_results.index:
        rtnote = query_results.rtnote[i]
        note_id = str(rtnote['id'])
        skip = query_results.skip[i]
        deck = query_results.deckName[i]
        model = query_results.modelName[i]
        use_md = query_results.useMarkdown[i]
        md_sty = query_results.markdownStyle[i]
        md_lineno = query_results.markdownLineNums[i]
        md_tablen = query_results.markdownTabLength[i]
        md_mathext = query_results.useMarkdownMathExt[i]
        tags = sorted(query_results.tags[i].replace(',','\n').split())
        fields = query_results.fields[i]
        media = query_results.media[i]
        description = "{}:{}".format(note_id, fields)

        if self.opts.question:
          log.info("*** ID: {}".format(note_id))
          log.info("--- Should skip: {}".format(skip))
          log.info("--- Note tags:")
          log.info(rtyaml.dump(tags))
          log.info("--- Note annotations:")
          log.info(rtyaml.dump(query_results.annotations[i]))
          log.info("--- Note fields:")
          log.info(rtyaml.dump(fields))
          log.info("--- Raw fields:")
          log.info(fields)
          log.info("")
          continue

        if skip:
          log.info("Skipping note with ID: {}".format(note_id))
          continue

        log.info("Processing note with ID: {}".format(note_id))
        log.debug("Note fields: {}".format(fields))

        # Check for note with given ID.
        # Get info for existing note.
        creating_new_note = True
        note_info = self.anki.notesInfo([note_id])

        if note_info.get("error", None) or not note_info['result'][0]:
          if self.opts.annotations:
            log.info("Can't find note with ID %s; skipping annotations for this note.", note_id)
            continue
          else:
            log.info("Can't find note with ID %s; a new note will be created.", note_id)
        else:
          creating_new_note = False

        note_templ_vars = dict(file_templ_vars)
        note_templ_vars['note_id'] = note_id
        note_uuid1 = uuid.uuid1()
        note_templ_vars['note_uuid1'] = note_uuid1
        file_uuid1 = note_templ_vars['file_uuid1']

        if creating_new_note:
          # No provided ID; assume new note should be created.
          log.debug("Creating new note...")

          temporary_fields = { k: self.format_text(
            str(v),
            False,
            md_sty,
            md_lineno,
            md_tablen,
            md_mathext,
            **note_templ_vars
          ) for (k, v) in fields.items() }

          # Create, obtaining returned ID
          anki_result = self.anki.addNote(
            deck,
            model,
            temporary_fields,
            tags = tags
          )
          if anki_result.get("error", None):
            log.warning("Can't create note: %s", description)
          else:
            # Add ID to note_node
            note_id = anki_result['result']
            note_templ_vars['note_id'] = note_id
            prev_id, rtnote['id'] = rtnote['id'], note_id
            log.info("ID %s replaced with %s.", prev_id, note_id)

        log.debug("Updating note...")
        # Assume provided ID is valid for existing note to be updated.
        # Convert each field from Markdown (if `use_md` is True).

        # Special handling for the annotations field. If we can find this note
        # in Anki's flashcard deck, then we'll grab any annotations the user has
        # made for that note, and store them in the YAML file. If we are instead
        # creating a new note, we'll transfer any annotations from the YAML file
        # to the new note.
        #
        # Because of this special handling, we remove annotations from the
        # shallow copy of the note. We'll instead use the round-trip version.

        if self.opts.annotations:
          pass
        else:
          if annotations_field in fields:
            del fields[annotations_field]
          converted_fields = { k: self.format_text(
            str(v),
            use_md,
            md_sty,
            md_lineno,
            md_tablen,
            md_mathext,
            field_no,
            **note_templ_vars
          ) for (field_no, (k, v)) in enumerate(fields.items()) }
          for media_item in media:
            item_path = media_item['path']
            item_path = string.Template(item_path).safe_substitute(
              note_templ_vars
            )
            item_name = media_item.get('name', os.path.basename(item_path))
            item_name = string.Template(item_name).safe_substitute(
              note_templ_vars
            )

            log.info("Considering sending media item...")
            log.info("    local path: {}".format(item_path))
            log.info("    remote name: {}".format(item_name))
            anki_result = self.anki.statMediaFile(item_name)
            must_send_new_media_item = False
            item_data = None
            if anki_result.get("error", None):
              log.info("Can't get remote media file status (probably missing)...")
              must_send_new_media_item = True
            else:
              if not anki_result['result']:
                log.info("... Media item is not present on remote...")
                must_send_new_media_item = True
              else:
                log.info("... Media item is already present on remote...")
                log.info("... Reading local data...")
                item_data = open(item_path, 'rb').read()
                item_adler32 = zlib.adler32(item_data)
                remote_adler32 = anki_result['result']['adler32']
                log.info("    Remote checksum: {}".format(remote_adler32))
                log.info("    Local checksum: {}".format(item_adler32))
                if remote_adler32 == item_adler32:
                  log.info("... Remote checksum matches that of local version...")
                else:
                  log.info("... Remote checksum is not the same as local...")
                  must_send_new_media_item = True
            if must_send_new_media_item:
              if item_data is None:
                log.info("... Reading local data...")
                item_data = open(item_path, 'rb').read()
              log.info("... Encoding {} bytes of local data...".format(len(item_data)))
              item_base64 = base64.b64encode(item_data).decode("utf-8")
              log.info("... Sending {} bytes of encoded data to remote...".format(len(item_base64)))
              anki_result = self.anki.storeMediaFile(item_name, item_base64)
              if anki_result.get("error", None):
                log.warning("Can't store media file: %s", item_name)
            log.info("... Done with media item.")



        # If we found this note in Anki's flashcard deck, then we'll grab any
        # annotations the user has made for that note, and store them in the
        # YAML file. If we are instead creating a new note, we'll transfer any
        # annotations from the YAML file to the new note.
        if creating_new_note:
          log.debug("Transferring annotations to new note...")
          # Transfer annotations from YAML file to new note.
          annotations = rtnote['fields'].get(annotations_field, "")
        else:
          log.debug("Transferring annotations from existing note...")
          upstream_fields = note_info['result'][0]['fields']
          annotations = upstream_fields.get(annotations_field, dict(value = ''))['value']
          # Transfer annotations from existing note to YAML file.
          rtnote['fields'][annotations_field] = annotations

        if not self.opts.annotations:
          converted_fields[annotations_field] = annotations

          # Update converted note fields...
          result = self.anki.updateNoteFields(note_id, converted_fields)
          if result.get("error", None):
            log.warning("Can't update note: %s", description)
            continue

        # Update note tags...
        ## First get existing note tags.
        note_info = self.anki.notesInfo([note_id])
        if note_info.get("error", None):
          log.warning("Can't get tags for note: %s", description)
          continue

        current_tags = sorted(note_info['result'][0]['tags'])
        if current_tags != tags:
          rt_non_annot_tags = set(filter(lambda s: not s.startswith('ann:'), rtnote.get('tags', list())))
          non_annot_tags = set(filter(lambda s: not s.startswith('ann:'), tags))
          cur_non_annot_tags = set(filter(lambda s: not s.startswith('ann:'), current_tags))
          cur_annot_tags = set(filter(lambda s: s.startswith('ann:'), current_tags))
          tags = sorted(list(non_annot_tags.union(cur_annot_tags)))
          rt_tags = sorted(list(rt_non_annot_tags.union(cur_annot_tags)))
          rtnote['tags'] = rt_tags

          ## Remove existing note tags.
          log.info("Removing tags %s...", cur_non_annot_tags)
          result = self.anki.removeTags([note_id], " ".join(cur_non_annot_tags))
          if result.get("error", None):
            log.warning("Can't remove tags for note: %s", description)

          ## Add new note tags.
          log.info("Replacing with tags %s...", tags)
          result = self.anki.addTags([note_id], " ".join(tags))
          if result.get("error", None):
            log.warning("Can't add tags for note: %s", description)

          note_info = self.anki.notesInfo([note_id])



  def loadsend_files(self, filenames):
    log.info("Starting Anki edits...")
    result = self.anki.requireReset()
    if result.get("error", None):
      log.warning("Can't start Anki edits.")

    for input_filename in filenames:
      try:
        log.info('Trying file "%s"...', input_filename)
        self.loadsend_file(input_filename)
      except FileNotFoundError as e:
        log.warning('File not found: "%s"', e)

    log.info("Finishing Anki edits...")
    result = self.anki.maybeReset()
    if result.get("error", None):
      log.warning("Can't finish Anki edits.")


  def loadsend(self):
    return self.loadsend_files(self.opts.input)


def getdefaults():
  return dict(
    def_deckname = 'Default',
    def_modelname = 'BasicMathJax',
    def_annfield = 'Annotations',
    def_md_proc = 'Python-Markdown',
    def_md_sty = 'tango',
    def_md_tablen = 4,
    def_md_lineno = False,
    def_md_mathext = True,
    def_workdir = os.getcwd(),
  )

def getopts(defs = None):
  '''Parse command-line arguments.'''
  if defs is None: defs = getdefaults()

  parser = argparse.ArgumentParser(
    description = "Update Anki flashcards parsed from YAML."
  )
  parser.add_argument(
    "-d", "--debug",
    help = "Enable debugging output and routines",
    action = 'store_true',
    default = False,
  )
  parser.add_argument(
    "-q", "--query",
    help = "Query for filtering notes"
  )
  parser.add_argument(
    "input",
    help = "YAML file(s) with flashcard content",
    nargs = '+',
  )
  parser.add_argument(
    "-w", "--workdir",
    help = "Working directory (for intermediate files; default: {def_workdir})".format(**defs),
    default = defs['def_workdir'],
  )
  parser.add_argument(
    "--question",
    help = "Question mode; don't update Anki or YAML, just show query results",
    action = 'store_true',
    default = False,
  )
  parser.add_argument(
    "--annotations",
    help = "Annotations mode; don't update Anki fields, just sync annotations from Anki to YAML",
    action = 'store_true',
    default = False,
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
