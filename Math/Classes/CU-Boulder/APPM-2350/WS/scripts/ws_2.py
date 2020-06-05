import os, sys

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
base_dir = os.path.abspath(os.path.join(script_dir, '..'))
cur_path = os.path.abspath(__name__)
cur_dir = os.path.dirname(cur_path)
sys.path.insert(0, cur_dir)

from yml_generators import generate_hw_yml


variables = dict(
  course_title = "Calculus 3",
  course_abbrev = "APPM-2350",

  problem_type = "Recitation Worksheet",
  problem_abbrev = "Ws",

  assignment_num = "02",
  assignment_tag = "APPM-2350-WS02",
  sections = "SVEC 10.3 to 10.4",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  base_dir = base_dir,
  header_file = os.path.join(base_dir, "scripts/WS_header.yml"),
  note_file = os.path.join(base_dir, "scripts/WS_note.yml"),
)

generate_hw_yml(variables, 10)
