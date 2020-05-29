from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "12",
  chapter_title = "Vectors and the Geometry of Space",
  #chapter_tag = "CET-12-VectorsAndTheGeometryOfSpace",

  section_num = "01",
  section_title = "Three-Dimensional Coordinate Systems",
  #section_tag = "CET-12.01-ThreeDimensionalCoordinateSystems",

  problem_type = "Exercise",
  problem_abbrev = "Xs",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Exercises_header.yml",
  note_file = "programmatic/Exercise_note.yml",
  output_file = "12.01.Exercises.yml",
)

generate_yml(variables, 48)
