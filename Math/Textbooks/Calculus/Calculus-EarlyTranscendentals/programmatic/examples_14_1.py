from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "14",
  chapter_title = "Partial Derivatives",

  section_num = "01",
  section_title = "Functions of Several Variables",

  problem_type = "Example",
  problem_abbrev = "Xm",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Examples_header.yml",
  note_file = "programmatic/Example_note.yml",
  output_file = "14.01.Examples.yml",
)

generate_yml(variables, [1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
