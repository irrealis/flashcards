from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "14",
  chapter_title = "Partial Derivatives",

  section_num = "07-AP",
  section_title = "Applied Project - Designing a Dumpster",

  problem_type = "Exercise",
  problem_abbrev = "Xs",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Exercises_header.yml",
  note_file = "programmatic/Exercise_note.yml",
  output_file = "14.07-AP.Exercises.yml",
)

generate_yml(variables, 4)
