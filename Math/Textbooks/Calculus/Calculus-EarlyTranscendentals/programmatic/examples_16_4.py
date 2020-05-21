from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "16",
  chapter_title = "Vector Calculus",

  section_num = "04",
  section_title = "Green's Theorem",
  section_tag = "CET-16.04-GreensTheorem",

  problem_type = "Example",
  problem_abbrev = "Xm",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Examples_header.yml",
  note_file = "programmatic/Example_note.yml",
  output_file = "16.04.Examples.yml",
)

generate_yml(variables, 5)
