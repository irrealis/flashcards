from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "14",
  chapter_title = "Partial Derivatives",

  section_num = "04",
  section_title = "Tangent Planes and Linear Approximations",

  problem_type = "Exercise",
  problem_abbrev = "Xs",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Exercises_header.yml",
  note_file = "programmatic/Exercise_note.yml",
  output_file = "14.04.Exercises.yml",
)

generate_yml(variables, 46)
