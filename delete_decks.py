#!/usr/bin/env python3

from anki_connect_client import AnkiConnectClient

import argparse


def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Delete Anki flashcard decks."
  )
  parser.add_argument(
    "-c", "--cards-too",
    action = 'store_true',
    default = False,
    help = "delete cards in deck (otherwise move to Default)"
  )
  parser.add_argument(
    "decks",
    nargs = '+',
    help = "names of Anki decks to delete"
  )
  return parser.parse_args()

def main():
  cmdline_args = parse_cmdline()
  print("cmdline_args:", cmdline_args)
  connection = AnkiConnectClient()
  connection.send(
    action = "deleteDecks",
    params = dict(
      decks = cmdline_args.decks,
      cardsToo = True
      #cardsToo = cmdline_args.cards_too
    )
  )

  print("\nDone.\n")

if __name__ == "__main__":
  main()
