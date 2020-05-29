import math, os, string

def pascal_case(text):
  return ''.join(x for x in text.title() if not x.isspace())
  
def generate_yml(variables, problems):

  if type(problems) is int:
    problems = range(1, problems + 1)

  problem_num_format_str = "{{i:0{n}}}".format(n = math.ceil(math.log10(max(problems)+1)))
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
    for i in problems:
      output_file.write(note_template.substitute(variables, problem_num = problem_num_format_str.format(i = i)))
    


def generate_hw_yml(variables, problems):

  if type(problems) is int:
    problems = range(1, problems + 1)

  problem_num_format_str = "{{i:0{n}}}".format(n = math.ceil(math.log10(max(problems)+1)))

  if not 'course_tag' in variables:
    course_tag = '{course_abbrev}-{course_pascal_case}'.format(
      **variables,
      course_pascal_case = pascal_case(variables['course_title']),
    )
    variables['course_tag'] = course_tag
    
  if not 'assignment_tag' in variables:
    assignment_tag = '{course_abbrev}-{problem_abbrev}{assignment_num}'.format(
      **variables,
    )
    variables['assignment_tag'] = assignment_tag

  if not 'output_file' in variables:
    output_fnam = '{base_dir}/{assignment_tag}.yml'.format(
      **variables,
    )
    variables['output_file'] = output_fnam

  header_fnam = variables['header_file']
  note_fnam = variables['note_file']
  output_fnam = variables['output_file']

  if os.path.exists(output_fnam):
    raise FileExistsError(f'{output_fnam}')


  with open(header_fnam, 'r') as header_file:
    header_template = string.Template(''.join(header_file.readlines()))
  with open(note_fnam, 'r') as note_file:
    note_template = string.Template(''.join(note_file.readlines()))
  with open(output_fnam, 'w') as output_file:
    output_file.write(header_template.substitute(variables))
    for i in problems:
      output_file.write(note_template.substitute(variables, problem_num = problem_num_format_str.format(i = i)))
    
