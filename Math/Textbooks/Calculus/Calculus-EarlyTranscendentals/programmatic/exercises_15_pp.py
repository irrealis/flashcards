from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "15",
  chapter_title = "Multiple Integrals",

  section_num = "PP",
  section_title = "Problems Plus",

  problem_type = "Exercise",
  problem_abbrev = "Xs",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Exercises_header.yml",
  note_file = "programmatic/Exercise_note.yml",
  output_file = "15.PP.Exercises.yml",
)

generate_yml(variables, 13)
