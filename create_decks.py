#!/usr/bin/env python3

from anki_connect_client import AnkiConnectClient

import argparse


def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Create Anki flashcard decks."
  )
  parser.add_argument(
    "decks",
    nargs = '+',
    help = "names of Anki decks to create"
  )
  return parser.parse_args()

def main():
  cmdline_args = parse_cmdline()
  connection = AnkiConnectClient()
  for deck in cmdline_args.decks:
    connection.send(
      action = "createDeck",
      params = dict(
        deck = deck
      )
    )

  print("\nDone.\n")

if __name__ == "__main__":
  main()
