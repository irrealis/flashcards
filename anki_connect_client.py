import http.client, json, logging

log = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler()
log.addHandler(log_hdlr)


class AnkiConnectException(Exception):
  pass


class AnkiConnectClientBase(object):
  server_version = 6

  def __init__(self, hostname = None, port = None):
    self.connection = None
    self.connect(hostname, port)

  def __del__(self):
    self.close()

  def report_anki_error(self, result, message, *extra_args):
    log.warning(message, *extra_args)
    log.warning("\nAnkiConnect error description:\n %s", result["error"])

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

    Returns both HTTP response and any data received from AnkiConnect.
    '''
    # To simplify calling `send_as_json`, named parameters can be used in
    # place of a data dict.
    if data is None: data = d

    # If AnkiConnect version isn't supplied, use this class's default.
    if version is None: version = AnkiConnectClientBase.server_version
    data.setdefault("version", version)
    json_data = json.dumps(data)
    http_response = self.send_raw(json_data)
    json_result_data = http_response.read()
    result_data = json.loads(json_result_data)
    return http_response, result_data

  def send(self, data = None, version = None, **d):
    '''
    Simplified send of data to AnkiConnect.

    Returns any data received from AnkiConnect.
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


class AnkiConnectClient(AnkiConnectClientBase):
  def _check(self, response, result, message, *extra_args):
    if result.get("error", None):
      self.report_anki_error(result, message, *extra_args)
      log.warning("HTTP status: %s", response.status)
      log.warning("HTTP reason: %s", response.reason)


  ## Miscellaneous

  def version(self):
    """
    Gets the version of the AnkiConnect API exposed by AnkiConnectClient. AnkiConnectClient currently exposes AnkiConnect version 6.

    This should be the first call you make to make sure that your application and AnkiConnect are able to communicate properly with each other. New versions of AnkiConnect are backwards compatible; as long as you are using actions which are available in the reported AnkiConnect version or earlier, everything should work fine.

    Sample call: anki_connect_client.version()

    Sample result:
    {
        "result": 6,
        "error": null
    }
    """
    response, result = self.send_as_json(action = "version")
    self._check(response, result,
      "Error getting AnkiConnect version"
    )
    return result

  def upgrade(self):
    """
    Displays a confirmation dialog box in Anki asking the user if they wish to upgrade AnkiConnect to the latest version from the project's master branch on GitHub. Returns a boolean value indicating if the plugin was upgraded or not.

    Sample call: anki_connect_client.upgrade()

    Sample result:
    {
        "result": true,
        "error": null
    }
    """
    response, result = self.send_as_json(action = "upgrade")
    self._check(response, result, "Error upgrading AnkiConnect")
    return result

  def sync(self):
    """
    Synchronizes the local anki collections with ankiweb.

    Sample call: anki_connect_client.sync()

    Sample result:
    {
        "result": null,
        "error": null
    }
    """
    response, result = self.send_as_json(action = "sync")
    self._check(response, result, "Error syncing")
    return result


  ## Decks

  def deckNames(self):
    """
    Gets the complete list of deck names for the current user.

    Sample call: anki_connect_client.deckNames()

    Sample result:
    {
        "result": ["Default"],
        "error": null
    }
    """
    response, result = self.send_as_json(action = "deckNames")
    self._check(response, result,
      "Error getting deck names"
    )
    return result

  def deckNamesAndIds(self):
    """
    Gets the complete list of deck names and their respective IDs for the current user.

    Sample call: anki_connect_client.deckNamesAndIds()

    Sample result:
    {
        "result": {"Default": 1},
        "error": null
    }
    """
    response, result = self.send_as_json(action = "deckNamesAndIds")
    self._check(response, result,
      "Error getting deck names and IDs"
    )
    return result

  def getDecks(self, cards):
    """
    Accepts an array of card IDs and returns an object with each deck name as a key, and its value an array of the given cards which belong to it.

    Sample call:

    anki_connect_client.getDecks(
      cards = [1502298036657, 1502298033753, 1502032366472]
    )

    Sample result:
    {
        "result": {
            "Default": [1502032366472],
            "Japanese::JLPT N3": [1502298036657, 1502298033753]
        },
        "error": null
    }
    """
    response, result = self.send_as_json(action = "getDecks", params = dict(
      cards = cards
    ))
    self._check(response, result,
      "Error getting decks for cards %s", cards
    )
    return result

  def createDeck(self, deck):
    """
    Create a new empty deck. Will not overwrite a deck that exists with the same name.

    Sample request:

    anki_connect_client.createDeck(
      deck = "Japanese::Tokyo"
    )

    Sample result:
    {
        "result": 1519323742721,
        "error": null
    }
    """
    response, result = self.send_as_json(action = "createDeck", params = dict(
      deck = deck
    ))
    self._check(response, result,
      'Error creating deck "%s"', deck
    )
    return result

  def changeDeck(self, cards, deck):
    """
    TODO
    """
    response, result = self.send_as_json(action = "changeDeck", params = dict(
      cards = cards,
      deck = deck
    ))
    self._check(response, result,
      'Error changing to deck "%s" for cards %s', deck, cards
    )
    return result

  def deleteDecks(self, decks, cardsToo = False):
    """
    Deletes decks with the given names. If cardsToo is true (defaults to false if unspecified), the cards within the deleted decks will also be deleted; otherwise they will be moved to the default deck.

    Sample request:

    anki_connect_client.deleteDecks(
      decks = ["Japanese::JLPT N5", "Easy Spanish"],
      cardsToo = true
    )

    Sample result:
    {
        "result": null,
        "error": null
    }
    """
    response, result = self.send_as_json(action = "deleteDecks", params = dict(
      decks = decks, cardsToo = cardsToo
    ))
    self._check(response, result,
      "Error deleting decks %s", decks
    )
    return result

  def getDeckConfig(self, deck):
    """
    TODO
    """
    response, result = self.send_as_json(action = "getDeckConfig", params = dict(
      deck = deck
    ))
    self._check(response, result,
      'Error getting configuration for deck "%s"', deck
    )
    return result

  def saveDeckConfig(self, config):
    """
    TODO
    """
    response, result = self.send_as_json(action = "saveDeckConfig", params = dict(
      config = config
    ))
    self._check(response, result,
      'Error saving configuration %s', config
    )
    return result

  def setDeckConfigId(self, decks, configId):
    """
    TODO
    """
    response, result = self.send_as_json(action = "setDeckConfigId", params = dict(
      decks = decks,
      configId = configId,
    ))
    self._check(response, result,
      'Error setting configuration %s for decks %s', configId, decks
    )
    return result

  def cloneDeckConfigId(self, name, cloneFrom):
    """
    TODO
    """
    response, result = self.send_as_json(action = "cloneDeckConfigId", params = dict(
      name = name,
      cloneFrom = cloneFrom,
    ))
    self._check(response, result,
      'Error cloning configuration %s as %s', cloneFrom, name
    )
    return result

  def removeDeckConfigId(self, configId):
    """
    TODO
    """
    response, result = self.send_as_json(action = "removeDeckConfigId", params = dict(
      configId = configId,
    ))
    self._check(response, result,
      'Error removing configuration %s', configId
    )
    return result


  ## Models

  def modelNames(self):
    """
    TODO
    """
    response, result = self.send_as_json(action = "modelNames")
    self._check(response, result,
      'Error getting model names'
    )
    return result

  def modelNamesAndIds(self):
    """
    TODO
    """
    response, result = self.send_as_json(action = "modelNamesAndIds")
    self._check(response, result,
      'Error getting model names and IDs'
    )
    return result

  def modelFieldNames(self, modelName):
    """
    TODO
    """
    response, result = self.send_as_json(action = "modelFieldNames", params = dict(
      modelName = modelName
    ))
    self._check(response, result,
      'Error getting field names for model "%s"', modelName
    )
    return result

  def modelFieldsOnTemplates(self, modelName):
    """
    TODO
    """
    response, result = self.send_as_json(action = "modelFieldsOnTemplates", params = dict(
      modelName = modelName
    ))
    self._check(response, result,
      'Error getting per-template field names for model "%s"', modelName
    )
    return result


  ## Models

  def addNote(self, deckName, modelName, fields, tags = None, audio = None):
    """
    TODO
    """
    note = dict(
      deckName = deckName,
      modelName = modelName,
      fields = fields,
    )
    if tags is not None:
      note['tags'] = tags
    if audio is not None:
      note['audio'] = audio
    print("note:")
    print(note)
    response, result = self.send_as_json(action = "addNote", params = dict(
      note = note
    ))
    self._check(response, result,
      'Error adding note %s', note
    )
    return result

  def addNotes(self, notes):
    """
    TODO
    """
    response, result = self.send_as_json(action = "addNotes", params = dict(
      notes = notes
    ))
    self._check(response, result,
      'Error adding notes %s', notes
    )
    return result

  def canAddNotes(self, notes):
    """
    TODO
    """
    response, result = self.send_as_json(action = "canAddNotes", params = dict(
      notes = notes
    ))
    self._check(response, result,
      'Error checking whether notes can be added: %s', notes
    )
    return result

  def updateNoteFields(self, id, fields):
    """
    TODO
    """
    note = dict(
      id = id,
      fields = fields,
    )
    response, result = self.send_as_json(action = "updateNoteFields", params = dict(
      note = note
    ))
    self._check(response, result,
      'Error updating note %s with fields %s', id, fields
    )
    return result

  def addTags(self, notes, tags):
    """
    TODO
    """
    response, result = self.send_as_json(action = "addTags", params = dict(
      notes = notes,
      tags = tags,
    ))
    self._check(response, result,
      'Error adding tags %s for notes %s', tags, notes
    )
    return result

  def removeTags(self, notes, tags):
    """
    TODO
    """
    response, result = self.send_as_json(action = "removeTags", params = dict(
      notes = notes,
      tags = tags,
    ))
    self._check(response, result,
      'Error removing tags %s for notes %s', tags, notes
    )
    return result

  def getTags(self):
    """
    TODO
    """
    response, result = self.send_as_json(action = "getTags")
    self._check(response, result,
      'Error getting tags'
    )
    return result

  def findNotes(self, query):
    """
    TODO
    """
    response, result = self.send_as_json(action = "findNotes", params = dict(
      query = query
    ))
    self._check(response, result,
      'Error searching notes using query "%s"', query
    )
    return result

  def notesInfo(self, notes):
    """
    TODO
    """
    response, result = self.send_as_json(action = "notesInfo", params = dict(
      notes = notes
    ))
    self._check(response, result,
      'Error getting info for notes %s', notes
    )
    return result
