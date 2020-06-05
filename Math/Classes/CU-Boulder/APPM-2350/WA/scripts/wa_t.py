import os, sys

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
base_dir = os.path.abspath(os.path.join(script_dir, '..'))
cur_path = os.path.abspath(__name__)
cur_dir = os.path.dirname(cur_path)
sys.path.insert(0, cur_dir)

script_fmt = '''
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

  problem_type = "WebAssign",
  problem_abbrev = "WA-",

  assignment_num = "{assignment_num}",
  sections = "SVEC {sections}",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  base_dir = "{base_dir}",
  header_file = os.path.join(base_dir, "scripts/WA_header.yml"),
  note_file = os.path.join(base_dir, "scripts/WA_note.yml"),
)

generate_hw_yml(variables, {problems})
'''

webassigns = [
  ('10.01', 10),
  ('10.02', 10),
  ('10.03', 12),
  ('10.04', 11),
  ('10.05', 10),
  ('10.06', 11),
  ('10.07', 10),
  ('10.08,09', 10),

  ('11.01', 10),
  ('11.02', 10),
  ('11.03', 10),
  ('11.04', 10),
  ('11.05', 10),
  ('11.06', 10),
  ('11.07', 10),
  ('11.08', 10),

  ('12.01,02', 10),
  ('12.03', 10),
  ('12.04', 10),
  ('12.05', 10),
  ('12.06,07', 10),
  ('12.08', 10),

  ('13.01,02', 10),
  ('13.03', 10),
  ('13.04', 10),
  ('13.05', 10),
  ('13.06sa,07', 10),
  ('13.08', 10),
  ('13.09', 10),
]

for wa, pc in webassigns:
  script = script_fmt.format(
    assignment_num = wa,
    sections = wa,
    base_dir = base_dir,
    problems = pc,
  )
  output_fnam = '{script_dir}/WA-{assignment_tag}.py'.format(
    script_dir = script_dir,
    assignment_tag = wa,
  )
  #print("***")
  #print(output_fnam)
  #print("---")
  #print(script)
  with open(output_fnam, 'w') as output_file:
    output_file.write(script)

