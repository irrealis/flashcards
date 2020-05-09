from yml_generators import generate_yml

variables = dict(
  textbook_title = "Calculus - Early Trancendentals",
  textbook_abbrev = "CET",
  textbook_tag = "Calculus-EarlyTrancendentals",

  chapter_num = "12",
  chapter_title = "Vectors and the Geometry of Space",
  #chapter_tag = "CET-12-VectorsAndTheGeometryOfSpace",

  section_num = "02",
  section_title = "Vectors",
  #section_tag = ""

  problem_type = "Example",
  problem_abbrev = "Xm",

  deck_name = "Staging",
  model_name = "PWeave",
  markdown_tab_length = "2",
  string_templ_delim = "¢",

  header_file = "programmatic/Examples_header.yml",
  note_file = "programmatic/Example_note.yml",
  output_file = "12.02.Examples.yml",
)

generate_yml(variables, 7)
