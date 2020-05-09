import math, os, string

def pascal_case(text):
  return ''.join(x for x in text.title() if not x.isspace())
  
def generate_yml(variables, problem_count):

  problem_num_format_str = "{{i:0{n}}}".format(n = math.ceil(math.log10(problem_count + 1)))
  header_fnam = variables['header_file']
  note_fnam = variables['note_file']
  output_fnam = variables['output_file']

  if os.path.exists(output_fnam):
    raise FileExistsError(f'{output_fnam}')
    

  if not 'chapter_tag' in variables:
    chapter_tag = '{textbook_abbrev}-{chapter_num}-{chapter_pascal_case}'.format(
      **variables,
      chapter_pascal_case = pascal_case(variables['chapter_title']),
    )
    variables['chapter_tag'] = chapter_tag
  
  if not 'section_tag' in variables:
    section_tag = '{textbook_abbrev}-{chapter_num}.{section_num}-{section_pascal_case}'.format(
      **variables,
      section_pascal_case = pascal_case(variables['section_title']),
    )
    variables['section_tag'] = section_tag
  
  with open(header_fnam, 'r') as header_file:
    header_template = string.Template(''.join(header_file.readlines()))
  with open(note_fnam, 'r') as note_file:
    note_template = string.Template(''.join(note_file.readlines()))
  with open(output_fnam, 'w') as output_file:
    output_file.write(header_template.substitute(variables))
    for i in range(1, problem_count + 1):
      output_file.write(note_template.substitute(variables, problem_num = problem_num_format_str.format(i = i)))
    
