from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "15",
  chapter_title = "Multiple Integrals",

  section_num = "06",
  section_title = "Triple Integrals",

  problem_type = "Example",
  problem_abbrev = "Xm",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Examples_header.yml",
  note_file = "programmatic/Example_note.yml",
  output_file = "15.06.Examples.yml",
)

generate_yml(variables, 6)
