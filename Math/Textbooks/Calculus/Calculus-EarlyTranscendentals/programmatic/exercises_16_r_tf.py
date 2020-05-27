from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "16",
  chapter_title = "Vector Calculus",

  section_num = "R-TF",
  section_title = "Review",

  problem_type = "True-False",
  problem_abbrev = "TF",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Exercises_header.yml",
  note_file = "programmatic/Exercise_note.yml",
  output_file = "16.R-TF.Exercises.yml",
)

generate_yml(variables, 13)
