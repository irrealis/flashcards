#!/usr/bin/env python3

import yaml
import argparse, http.client, json


class AnkiConnectException(Exception):
  pass


class AnkiConnectClient(object):
  server_version = 6

  def __init__(self, hostname = None, port = None):
    self.connection = None
    self.connect(hostname, port)

  def __del__(self):
    self.close()

  def connect(self, hostname = None, port = None):
    '''Open HTTP connection to AnkiConnect.'''
    self.close()
    if hostname is None: hostname = '127.0.0.1'
    if port is None: port = 8765
    self.hostname = hostname
    self.port = port
    self.connection = http.client.HTTPConnection(self.hostname, self.port)

  def close(self):
    '''Close HTTP connection to AnkiConnect.'''
    if self.connection: self.connection.close()

  def send_raw(self, data):
    '''Send raw data to AnkiConnect.'''
    self.close()
    self.connection.request("POST", "", data)
    response = self.connection.getresponse()
    return response

  def send_as_json(self, data = None, version = None, **d):
    '''
    Convert data to JSON, then send to AnkiConnect.

    Returns both HTTP response and any data from AnkiConnect.
    '''
    # To simplify calling `send_as_json`, named parameters can be used in
    # place of a data dict.
    if data is None: data = d

    # If AnkiConnect version isn't supplied, use this class's default.
    if version is None: version = AnkiConnectClient.server_version
    data.setdefault("version", version)
    json_data = json.dumps(data)
    http_response = self.send_raw(json_data)
    json_result_data = http_response.read()
    result_data = json.loads(json_result_data)
    return http_response, result_data

  def send(self, data = None, version = None, **d):
    '''
    Simplified send of data to AnkiConnect in JSON format.

    Returns any data from AnkiConnect.
    '''
    http_response, result_data = self.send_as_json(data, version, **d)

    # Propagate error if indicated by non-None value in "error" field.
    # Note: AnkiConnect doesn't use this field for certain errors.
    if result_data["error"] is not None:
      msg = "error: {}, http status: {}, http reason: {}".format(
        result_data["error"],
        http_response.status,
        http_response.reason,
      )
      raise AnkiConnectException(msg)

    # If no error indicated in "error" field, return data from AnkiConnect.
    return result_data


def parse_cmdline():
  '''Parse command-line arguments.'''
  parser = argparse.ArgumentParser(
    description = "Send Anki flashcards parsed from YAML."
  )
  parser.add_argument(
    "input",
    help = "YAML file with flashcard content"
  )
  return parser.parse_args()


def data_to_flashcards_params(data):
  '''Convert data to format accepted by AnkiConnect.'''
  params = dict(
    notes = [
      dict(
        tags = data["tags"],
        deckName = data["deckName"],
        modelName = data["modelName"],
        fields = {
          k: v.
            replace('\n', '<br>').
            replace(' ', '&nbsp;')
          for (k, v) in note.items()
        }
      )
      for note in data["notes"]
    ]
  )
  return params


def try_anki_connect_version(connection):
  return connection.send(action = "version")


def try_send_flashcards_to_anki(connection, params):
  return connection.send(
    action = "addNotes",
    params = params
  )


def main():
  cmdline_args = parse_cmdline()

  # Load and parse flashcard data from input YAML file.
  with open(cmdline_args.input) as yaml_file:
    flashcard_data = yaml.load(yaml_file)
  flashcard_params = data_to_flashcards_params(flashcard_data)

  # Send data to AnkiConnect with request to create flashcards.
  connection = AnkiConnectClient()
  result_data = try_send_flashcards_to_anki(connection, flashcard_params)

  # Report any errors.
  notes = flashcard_data["notes"]
  errors = (result is None for result in result_data["result"])
  for note, error in zip(notes, errors):
    if error:
      print("\n*** Couldn't add note: {}".format(note))


if __name__ == "__main__":
  main()
