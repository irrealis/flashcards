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
  ('10.01', 5),
  ('10.02', 5),
  ('10.03', 5),
  ('10.04', 5),
  ('10.05', 5),
  ('10.06', 5),
  ('10.07', 5),
  ('10.08,09', 5),

  ('11.01', 5),
  ('11.02', 5),
  ('11.03', 5),
  ('11.04', 5),
  ('11.05', 5),
  ('11.06', 5),
  ('11.07', 5),
  ('11.08', 5),

  ('12.01,02', 5),
  ('12.03', 5),
  ('12.04', 5),
  ('12.05', 5),
  ('12.06,07', 5),
  ('12.08', 5),

  ('13.01,02', 5),
  ('13.03', 5),
  ('13.04', 5),
  ('13.05', 5),
  ('13.06sa,07', 5),
  ('13.08', 5),
  ('13.09', 5),
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

