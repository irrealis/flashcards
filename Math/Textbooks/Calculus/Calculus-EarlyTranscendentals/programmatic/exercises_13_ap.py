from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "13",
  chapter_title = "Vector Functions",

  section_num = "AP",
  section_title = "Applied Project: Kepler's Laws",
  section_tag = "CET-13.AP-KeplersLaws",

  problem_type = "Applied Project",
  problem_abbrev = "AP",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Exercises_header.yml",
  note_file = "programmatic/Exercise_note.yml",
  output_file = "13.AP.Exercises.yml",
)

generate_yml(variables, 4)
