import http.client, json, logging

log = logging.getLogger(__name__)
log_hdlr = logging.StreamHandler()
log.addHandler(log_hdlr)


class AnkiException(Exception):
  pass


class AnkiClientBase(object):
  server_version = 6

  def __init__(self, hostname = None, port = None):
    self.connection = None
    self.connect(hostname, port)

  def __del__(self):
    self.close()

  def report_anki_error(self, result, message, *extra_args):
    log.warning(message, *extra_args)
    log.warning("\n*** Anki error description:\n %s\n", result["error"])

  def connect(self, hostname = None, port = None):
    '''Open HTTP connection to Anki.'''
    self.close()
    if hostname is None: hostname = 'localhost'
    if port is None: port = 8765
    self.hostname = hostname
    self.port = port
    self.connection = http.client.HTTPConnection(self.hostname, self.port)

  def close(self):
    '''Close HTTP connection to Anki.'''
    if self.connection: self.connection.close()

  def send_raw(self, data):
    '''Send raw data to Anki.'''
    self.close()
    self.connection.request("POST", "", data)
    response = self.connection.getresponse()
    return response

  def send_as_json(self, data = None, version = None, **d):
    '''
    Convert data to JSON, then send to Anki.

    Returns both HTTP response and any data received from Anki.
    '''
    # To simplify calling `send_as_json`, named parameters can be used in
    # place of a data dict.
    if data is None: data = d

    # If AnkiConnect version isn't supplied, use this class's default.
    if version is None: version = AnkiClientBase.server_version
    data.setdefault("version", version)
    json_data = json.dumps(data)
    http_response = self.send_raw(json_data)
    json_result_data = http_response.read()
    result_data = json.loads(json_result_data)
    return http_response, result_data

  def send(self, data = None, version = None, **d):
    '''
    Simplified send of data to Anki.

    Returns any data received from Anki.
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
      raise AnkiException(msg)

    # If no error indicated in "error" field, return data from Anki.
    return result_data


class AnkiClient(AnkiClientBase):
  def _check(self, response, result, message, *extra_args):
    if result.get("error", None):
      self.report_anki_error(result, message, *extra_args)
      log.warning("HTTP status: %s", response.status)
      log.warning("HTTP reason: %s", response.reason)


  ## Miscellaneous

  def version(self):
    """
    Gets the version of the AnkiConnect API exposed by AnkiClient. AnkiClient currently exposes AnkiConnect version 6.

    This should be the first call you make to make sure that your application and AnkiConnect are able to communicate properly with each other. New versions of AnkiConnect are backwards compatible; as long as you are using actions which are available in the reported AnkiConnect version or earlier, everything should work fine.

    Sample call:

      client.version()

    Sample result:

      {
        "result": 6,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "version")
    self._check(wr, r, "Error getting AnkiConnect version")
    return r

  def upgrade(self):
    """
    Displays a confirmation dialog box in Anki asking the user if they wish to upgrade AnkiConnect to the latest version from the project's master branch on GitHub. Returns a boolean value indicating if the plugin was upgraded or not.

    Sample call:

      client.upgrade()

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "upgrade")
    self._check(wr, r, "Error upgrading AnkiConnect")
    return r

  def sync(self):
    """
    Synchronizes the local anki collections with ankiweb.

    Sample call:

      client.sync()

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "sync")
    self._check(wr, r, "Error syncing")
    return r


  ## Decks

  def deckNames(self):
    """
    Gets the complete list of deck names for the current user.

    Sample call:

      client.deckNames()

    Sample result:

      {
        "result": ["Default"],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "deckNames")
    self._check(wr, r,
      "Error getting deck names"
    )
    return r

  def deckNamesAndIds(self):
    """
    Gets the complete list of deck names and their respective IDs for the current user.

    Sample call:

      client.deckNamesAndIds()

    Sample result:

      {
        "result": {"Default": 1},
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "deckNamesAndIds")
    self._check(wr, r,
      "Error getting deck names and IDs"
    )
    return r

  def getDecks(self, cards):
    """
    Accepts an array of card IDs and returns an object with each deck name as a key, and its value an array of the given cards which belong to it.

    Sample call:

      client.getDecks(
        cards = [1502298036657, 1502298033753, 1502032366472]
      )

    Sample result:

      {
        "result": {
          "default": [1502032366472],
          "japanese::jlpt n3": [1502298036657, 1502298033753]
        },
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "getDecks", params = dict(
      cards = cards
    ))
    self._check(wr, r,
      "Error getting decks for cards %s", cards
    )
    return r

  def createDeck(self, deck):
    """
    Create a new empty deck. Will not overwrite a deck that exists with the same name.

    Sample request:

      client.createDeck(
        deck = "Japanese::Tokyo"
      )

    Sample result:

      {
        "result": 1519323742721,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "createDeck", params = dict(
      deck = deck
    ))
    self._check(wr, r,
      'Error creating deck "%s"', deck
    )
    return r

  def changeDeck(self, cards, deck):
    """
    Moves cards with the given IDs to a different deck, creating the deck if it doesn't exist yet.

    Sample request:

      client.changeDeck(
        cards = [1502098034045, 1502098034048, 1502298033753],
        deck = "Japanese::JLPT N3"
      )

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "changeDeck", params = dict(
      cards = cards,
      deck = deck
    ))
    self._check(wr, r,
      'Error changing to deck "%s" for cards %s', deck, cards
    )
    return r

  def deleteDecks(self, decks, cardsToo = False):
    """
    Deletes decks with the given names. If cardsToo is true (defaults to false if unspecified), the cards within the deleted decks will also be deleted; otherwise they will be moved to the default deck.

    Sample request:

      client.deleteDecks(
        decks = ["Japanese::JLPT N5", "Easy Spanish"],
        cardsToo = true
      )

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "deleteDecks", params = dict(
      decks = decks, cardsToo = cardsToo
    ))
    self._check(wr, r,
      "Error deleting decks %s", decks
    )
    return r

  def getDeckConfig(self, deck):
    """
    Gets the configuration group object for the given deck.

    Sample request:

      client.getDeckConfig(
        deck = "Default"
      )

    Sample result:

      {
        "result": {
          "lapse": {
            "leechFails": 8,
            "delays": [10],
            "minInt": 1,
            "leechAction": 0,
            "mult": 0
          },
          "dyn": false,
          "autoplay": true,
          "mod": 1502970872,
          "id": 1,
          "maxTaken": 60,
          "new": {
            "bury": true,
            "order": 1,
            "initialFactor": 2500,
            "perDay": 20,
            "delays": [1, 10],
            "separate": true,
            "ints": [1, 4, 7]
          },
          "name": "Default",
          "rev": {
            "bury": true,
            "ivlFct": 1,
            "ease4": 1.3,
            "maxIvl": 36500,
            "perDay": 100,
            "minSpace": 1,
            "fuzz": 0.05
          },
          "timer": 0,
          "replayq": true,
          "usn": -1
        },
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "getDeckConfig", params = dict(
      deck = deck
    ))
    self._check(wr, r,
      'Error getting configuration for deck "%s"', deck
    )
    return r

  def saveDeckConfig(self, config):
    """
    Saves the given configuration group, returning true on success or false if the ID of the configuration group is invalid (such as when it does not exist).

    Sample request:

      client.saveDeckConfig(
        config = {
          "lapse": {
            "leechFails": 8,
            "delays": [10],
            "minInt": 1,
            "leechAction": 0,
            "mult": 0
          },
          "dyn": false,
          "autoplay": true,
          "mod": 1502970872,
          "id": 1,
          "maxTaken": 60,
          "new": {
            "bury": true,
            "order": 1,
            "initialFactor": 2500,
            "perDay": 20,
            "delays": [1, 10],
            "separate": true,
            "ints": [1, 4, 7]
          },
          "name": "Default",
          "rev": {
            "bury": true,
            "ivlFct": 1,
            "ease4": 1.3,
            "maxIvl": 36500,
            "perDay": 100,
            "minSpace": 1,
            "fuzz": 0.05
          },
          "timer": 0,
          "replayq": true,
          "usn": -1
        }
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "saveDeckConfig", params = dict(
      config = config
    ))
    self._check(wr, r,
      'Error saving configuration %s', config
    )
    return r

  def setDeckConfigId(self, decks, configId):
    """
    Changes the configuration group for the given decks to the one with the given ID. Returns true on success or false if the given configuration group or any of the given decks do not exist.

    Sample request:

      client.setDeckConfigId(
        decks = ["Default"],
        configId = 1
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "setDeckConfigId", params = dict(
      decks = decks,
      configId = configId,
    ))
    self._check(wr, r,
      'Error setting configuration %s for decks %s', configId, decks
    )
    return r

  def cloneDeckConfigId(self, name, cloneFrom):
    """
    Creates a new configuration group with the given name, cloning from the group with the given ID, or from the default group if this is unspecified. Returns the ID of the new configuration group, or false if the specified group to clone from does not exist.

    Sample request:

      client.cloneDeckConfigId(
        name = "Copy of Default",
        cloneFrom = 1
      )

    Sample result:

      {
        "result": 1502972374573,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "cloneDeckConfigId", params = dict(
      name = name,
      cloneFrom = cloneFrom,
    ))
    self._check(wr, r,
      'Error cloning configuration %s as %s', cloneFrom, name
    )
    return r

  def removeDeckConfigId(self, configId):
    """
    Removes the configuration group with the given ID, returning true if successful, or false if attempting to remove either the default configuration group (ID = 1) or a configuration group that does not exist.

    Sample request:

      client.removeDeckConfigId(
        configId = 1502972374573
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "removeDeckConfigId", params = dict(
      configId = configId,
    ))
    self._check(wr, r,
      'Error removing configuration %s', configId
    )
    return r


  ## Models

  def modelNames(self):
    """
    Gets the complete list of model names for the current user.

    Sample request:

      client.modelNames()

    Sample result:

      {
        "result": ["Basic", "Basic (and reversed card)"],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "modelNames")
    self._check(wr, r,
      'Error getting model names'
    )
    return r

  def modelNamesAndIds(self):
    """
    Gets the complete list of model names and their corresponding IDs for the current user.

    Sample request:

      client.modelNamesAndIds()

    Sample result:

      {
        "result": {
          "Basic": 1483883011648,
          "Basic (and reversed card)": 1483883011644,
          "Basic (optional reversed card)": 1483883011631,
          "Cloze": 1483883011630
        },
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "modelNamesAndIds")
    self._check(wr, r,
      'Error getting model names and IDs'
    )
    return r

  def modelFieldNames(self, modelName):
    """
    Gets the complete list of field names for the provided model name.

    Sample request:

      client.modelFieldNames(
        modelName = "Basic"
      )

    Sample result:

      {
        "result": ["Front", "Back"],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "modelFieldNames", params = dict(
      modelName = modelName
    ))
    self._check(wr, r,
      'Error getting field names for model "%s"', modelName
    )
    return r

  def modelFieldsOnTemplates(self, modelName):
    """
    Returns an object indicating the fields on the question and answer side of each card template for the given model name. The question side is given first in each array.

    Sample request:

      client.modelFieldsOnTemplates(
        modelName = "Basic (and reversed card)"
      )

    Sample result:

      {
        "result": {
          "Card 1": [["Front"], ["Back"]],
          "Card 2": [["Back"], ["Front"]]
        },
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "modelFieldsOnTemplates", params = dict(
      modelName = modelName
    ))
    self._check(wr, r,
      'Error getting per-template field names for model "%s"', modelName
    )
    return r


  ## Models

  def addNote(self, deckName, modelName, fields, tags = None, audio = None):
    """
    Creates a note using the given deck and model, with the provided field values and tags. Returns the identifier of the created note created on success, and null on failure.

    Anki can download audio files and embed them in newly created notes. The corresponding audio note member is optional and can be omitted. If you choose to include it, the url and filename fields must be also defined. The skipHash field can be optionally provided to skip the inclusion of downloaded files with an MD5 hash that matches the provided value. This is useful for avoiding the saving of error pages and stub files. The fields member is a list of fields that should play audio when the card is displayed in Anki. The allowDuplicate member inside options group can be set to true to enable adding duplicate cards. Normally duplicate cards can not be added and trigger exception.

    Sample request:

      client.addNote(
        deckName = "Default",
        modelName = "Basic",
        fields = {
          "Front": "front content",
          "Back": "back content"
        },
        options = {
          "allowDuplicate": false
        },
        tags = [
          "yomichan"
        ],
        audio = {
          "url": "https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji=猫&kana=ねこ",
          "filename": "yomichan_ねこ_猫.mp3",
          "skipHash": "7e2c2f954ef6051373ba916f000168dc",
          "fields": [
            "Front"
          ]
        }
      )

    Sample result:

      {
        "result": 1496198395707,
        "error": null
      }
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
    wr, r = self.send_as_json(action = "addNote", params = dict(
      note = note
    ))
    self._check(wr, r,
      'Error adding note %s', note
    )
    return r

  def addNotes(self, notes):
    """
    Creates multiple notes using the given deck and model, with the provided field values and tags. Returns an array of identifiers of the created notes (notes that could not be created will have a null identifier). Please see the documentation for addNote for an explanation of objects in the notes array.

    Sample request:

      client.addNotes(
        notes = [
          {
            "deckName": "Default",
            "modelName": "Basic",
            "fields": {
              "Front": "front content",
              "Back": "back content"
            },
            "tags": [
              "yomichan"
            ],
            "audio": {
              "url": "https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji=猫&kana=ねこ",
              "filename": "yomichan_ねこ_猫.mp3",
              "skipHash": "7e2c2f954ef6051373ba916f000168dc",
              "fields": [
                "Front"
              ]
            }
          }
        ]
      )

    Sample result:

      {
        "result": [1496198395707, null],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "addNotes", params = dict(
      notes = notes
    ))
    self._check(wr, r,
      'Error adding notes %s', notes
    )
    return r

  def canAddNotes(self, notes):
    """
    Accepts an array of objects which define parameters for candidate notes (see addNote) and returns an array of booleans indicating whether or not the parameters at the corresponding index could be used to create a new note.

    Sample request:

      client.canAddNotes(
        notes = [
          {
            "deckName": "Default",
            "modelName": "Basic",
            "fields": {
              "Front": "front content",
              "Back": "back content"
            },
            "tags": [
              "yomichan"
            ]
          }
        ]
      )

    Sample result:

      {
        "result": [true],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "canAddNotes", params = dict(
      notes = notes
    ))
    self._check(wr, r,
      'Error checking whether notes can be added: %s', notes
    )
    return r

  def updateNoteFields(self, id, fields):
    """
    Modify the fields of an exist note.

    Sample request:

      client.updateNoteFields(
        id = 1514547547030,
        fields = {
          "Front": "new front content",
          "Back": "new back content"
        }
      )

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    note = dict(
      id = id,
      fields = fields,
    )
    wr, r = self.send_as_json(action = "updateNoteFields", params = dict(
      note = note
    ))
    self._check(wr, r,
      'Error updating note %s with fields %s', id, fields
    )
    return r

  def addTags(self, notes, tags):
    """
    Adds tags to notes by note ID. The `tags` argument should be a string made of space-separated concatenated tag strings.

    Sample request:

      client.addTags(
        notes = [1483959289817, 1483959291695],
        tags = "european-languages"
      )

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "addTags", params = dict(
      notes = notes,
      tags = tags,
    ))
    self._check(wr, r,
      'Error adding tags %s for notes %s', tags, notes
    )
    return r

  def removeTags(self, notes, tags):
    """
    Remove tags from notes by note ID. The `tags` argument should be a string made of space-separated concatenated tag strings.

    Sample request:

      client.removeTags(
        notes = [1483959289817, 1483959291695],
        tags = "european-languages"
      )

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "removeTags", params = dict(
      notes = notes,
      tags = tags,
    ))
    self._check(wr, r,
      'Error removing tags %s for notes %s', tags, notes
    )
    return r

  def getTags(self):
    """
    Gets the complete list of tags for the current user.

    Sample request:

      client.getTags()

    Sample result:

      {
        "result": ["european-languages", "idioms"],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "getTags")
    self._check(wr, r,
      'Error getting tags'
    )
    return r

  def findNotes(self, query):
    """
    Returns an array of note IDs for a given query. Same query syntax as guiBrowse.

    Sample request:

      client.findNotes(
        query = "deck:current"
      )

    Sample result:

      {
        "result": [1483959289817, 1483959291695],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "findNotes", params = dict(
      query = query
    ))
    self._check(wr, r,
      'Error searching notes using query "%s"', query
    )
    return r

  def notesInfo(self, notes):
    """
    Returns a list of objects containing for each note ID the note fields, tags, note type and the cards belonging to the note.

    Sample request:

      client.notesInfo(
        notes = [1502298033753]
      )

    Sample result:

      {
        "result": [
          {
            "noteId":1502298033753,
            "modelName": "Basic",
            "tags":["tag","another_tag"],
            "fields": {
              "Front": {"value": "front content", "order": 0},
              "Back": {"value": "back content", "order": 1}
            }
          }
        ],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "notesInfo", params = dict(
      notes = notes
    ))
    self._check(wr, r,
      'Error getting info for notes %s', notes
    )
    return r


  ## Cards

  def suspend(self, cards):
    """
    Suspend cards by card ID; returns true if successful (at least one card wasn't already suspended) or false otherwise.

    Sample request:

      client.suspend(
        cards = [1483959291685, 1483959293217]
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "suspend", params = dict(
      cards = cards
    ))
    self._check(wr, r, 'Error suspending cards %s', cards)
    return r

  def unsuspend(self, cards):
    """
    Unsuspend cards by card ID; returns true if successful (at least one card was previously suspended) or false otherwise.

    Sample request:

      client.unsuspend(
        cards = [1483959291685, 1483959293217]
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "unsuspend", params = dict(
      cards = cards
    ))
    self._check(wr, r, 'Error unsuspending cards %s', cards)
    return r

  def areSuspended(self, cards):
    """
    Returns an array indicating whether each of the given cards is suspended (in the same order).

    Sample request:

      client.areSuspended(
        cards = [1483959291685, 1483959293217]
      )

    Sample result:

      {
        "result": [false, true],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "areSuspended", params = dict(
      cards = cards
    ))
    self._check(wr, r, 'Error checking suspend status for cards %s', cards)
    return r

  def areDue(self, cards):
    """
    Returns an array indicating whether each of the given cards is due (in the same order). Note: cards in the learning queue with a large interval (over 20 minutes) are treated as not due until the time of their interval has passed, to match the way Anki treats them when reviewing.

    Sample request:

      client.areDue(
        cards = [1483959291685, 1483959293217]
      )

    Sample result:

      {
        "result": [false, true],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "areDue", params = dict(
      cards = cards
    ))
    self._check(wr, r, 'Error checking due status for cards %s', cards)
    return r

  def getIntervals(self, cards, complete = False):
    """
    Returns an array of the most recent intervals for each given card ID, or a 2-dimensional array of all the intervals for each given card ID when complete is true. Negative intervals are in seconds and positive intervals in days.

    Sample request 1:

      client.getIntervals(
        cards = [1502298033753, 1502298036657]
      )

    Sample result 1:

      {
        "result": [-14400, 3],
        "error": null
      }

    Sample request 2:

      client.getIntervals(
        cards = [1502298033753, 1502298036657],
        complete = true
      )

    Sample result 2:

      {
        "result": [
          [-120, -180, -240, -300, -360, -14400],
          [-120, -180, -240, -300, -360, -14400, 1, 3]
        ],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "getIntervals", params = dict(
      cards = cards,
      complete = complete
    ))
    self._check(wr, r, 'Error getting intervals for cards %s', cards)
    return r

  def findCards(self, query):
    """
    Returns an array of card IDs for a given query. Functionally identical to guiBrowse but doesn't use the GUI for better performance.

    Sample request:

      client.findCards(
        query = "deck:current"
      )

    Sample result:

      {
        "result": [1494723142483, 1494703460437, 1494703479525],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "findCards", params = dict(
      query = query
    ))
    self._check(wr, r, 'Error finding cards for query %s', query)
    return r

  def cardsToNotes(self, cards):
    """
    Returns an unordered array of note IDs for the given card IDs. For cards with the same note, the ID is only given once in the array.

    Sample request:

      client.cardsToNotes(
        cards = [1502098034045, 1502098034048, 1502298033753]
      )

    Sample result:

      {
        "result": [1502098029797, 1502298025183],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "cardsToNotes", params = dict(
      cards = cards
    ))
    self._check(wr, r, 'Error getting notes for cards %s', cards)
    return r

  def cardsInfo(self, cards):
    """
    Returns a list of objects containing for each card ID the card fields, front and back sides including CSS, note type, the note that the card belongs to, and deck name, as well as ease and interval.

    Sample request:

      client.cardsInfo(
        cards = [1498938915662, 1502098034048]
      )

    Sample result:

      {
        "result": [
          {
            "answer": "back content",
            "question": "front content",
            "deckName": "Default",
            "modelName": "Basic",
            "fieldOrder": 1,
            "fields": {
              "Front": {"value": "front content", "order": 0},
              "Back": {"value": "back content", "order": 1}
            },
            "css":"p {font-family:Arial;}",
            "cardId": 1498938915662,
            "interval": 16,
            "note":1502298033753
          },
          {
            "answer": "back content",
            "question": "front content",
            "deckName": "Default",
            "modelName": "Basic",
            "fieldOrder": 0,
            "fields": {
              "Front": {"value": "front content", "order": 0},
              "Back": {"value": "back content", "order": 1}
            },
            "css":"p {font-family:Arial;}",
            "cardId": 1502098034048,
            "interval": 23,
            "note":1502298033753
          }
        ],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "cardsInfo", params = dict(
      cards = cards
    ))
    self._check(wr, r, 'Error getting info for cards %s', cards)
    return r


  ## Media

  def storeMediaFile(self, filename, data):
    """
    Stores a file with the specified base64-encoded contents inside the media folder. To prevent Anki from removing files not used by any cards (e.g. for configuration files), prefix the filename with an underscore. These files are still synchronized to AnkiWeb.

    Sample request:

        client.storeMediaFile(
          filename = "_hello.txt",
          data = "SGVsbG8sIHdvcmxkIQ=="
        )

    Sample result:

      {
        "result": null,
        "error": null
      }

    Content of _hello.txt:

      Hello world!
    """
    wr, r = self.send_as_json(action = "storeMediaFile", params = dict(
      filename = filename,
      data = data,
    ))
    self._check(wr, r,
      'Error storing media file "%s"', filename
    )
    return r

  def retrieveMediaFile(self, filename):
    """
    Retrieves the base64-encoded contents of the specified file, returning false if the file does not exist.

    Sample request:

      client.retrieveMediaFile(
        filename = "_hello.txt"
      )

    Sample result:

      {
        "result": "SGVsbG8sIHdvcmxkIQ==",
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "retrieveMediaFile", params = dict(
      filename = filename
    ))
    self._check(wr, r, 'Error retrieving media file "%s"', filename)
    return r

  def deleteMediaFile(self, filename):
    """
    Deletes the specified file inside the media folder.

    Sample request:

      client.deleteMediaFile(
        filename = "_hello.txt"
      )

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "deleteMediaFile", params = dict(
      filename = filename
    ))
    self._check(wr, r, 'Error deleting media file "%s"', filename)
    return r


  ## Graphical

  def guiBrowse(self, query):
    """
    Invokes the Card Browser dialog and searches for a given query. Returns an array of identifiers of the cards that were found.

    Sample request:

      client.guiBrowse(
        query = "deck:current"
      )

    Sample result:

      {
        "result": [1494723142483, 1494703460437, 1494703479525],
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiBrowse", params = dict(
      query = query
    ))
    self._check(wr, r, 'Error browsing GUI for query %s', query)
    return r

  def guiAddCards(self):
    """
    Invokes the Add Cards dialog.

    Sample request:

      client.guiAddCards()

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "GuiAddCards")
    self._check(wr, r, 'Error invoking Add Cards dialog')
    return r

  def guiCurrentCard(self):
    """
    Returns information about the current card or null if not in review mode.

    Sample request:

      client.guiCurrentCard()

    Sample result:

      {
        "result": {
          "answer": "back content",
          "question": "front content",
          "deckName": "Default",
          "modelName": "Basic",
          "fieldOrder": 0,
          "fields": {
            "Front": {"value": "front content", "order": 0},
            "Back": {"value": "back content", "order": 1}
          },
          "template": "Forward",
          "cardId": 1498938915662,
          "buttons": [1, 2, 3]
        },
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiCurrentCard")
    self._check(wr, r, 'Error getting info for current card')
    return r

  def guiStartCardTimer(self):
    """
    Starts or resets the timerStarted value for the current card. This is useful for deferring the start time to when it is displayed via the API, allowing the recorded time taken to answer the card to be more accurate when calling guiAnswerCard.

    Sample request:

      client.guiStartCardTimer()

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiStartCardTimer")
    self._check(wr, r, 'Error starting/resetting timerStarted value for current card')
    return r

  def guiShowQuestion(self):
    """
    Shows question text for the current card; returns true if in review mode or false otherwise.

    Sample request:

      client.guiShowQuestion()

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiShowQuestion")
    self._check(wr, r, 'Error showing question for current card')
    return r

  def guiShowAnswer(self):
    """
    Shows answer text for the current card; returns true if in review mode or false otherwise.

    Sample request:

      client.guiShowAnswer()

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiShowAnswer")
    self._check(wr, r, 'Error showing answer for current card')
    return r

  def guiAnswerCard(self, ease):
    """
    Answers the current card; returns true if succeeded or false otherwise. Note that the answer for the current card must be displayed before before any answer can be accepted by Anki.

    Sample request:

      client.guiAnswerCard(
        ease = 1
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiAnswerCard", params = dict(
      ease = ease
    ))
    self._check(wr, r, 'Error answering current card')
    return r

  def guiDeckOverview(self, name):
    """
    Opens the Deck Overview dialog for the deck with the given name; returns true if succeeded or false otherwise.

    Sample request:

      client.guiDeckOverview(
        name = "Default"
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiDeckOverview", params = dict(
      name = name
    ))
    self._check(wr, r, 'Error opening Deck Overview dialog for deck with name "%s"', name)
    return r

  def guiDeckBrowser(self):
    """
    Opens the Deck Browser dialog.

    Sample request:

      client.guiDeckBrowser()

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiDeckBrowser")
    self._check(wr, r, 'Error opening Deck Browser dialog')
    return r

  def guiDeckReview(self, name):
    """
    Starts review for the deck with the given name; returns true if succeeded or false otherwise.

    Sample request:

      client.guiDeckReview(
        name = "Default"
      )

    Sample result:

      {
        "result": true,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiDeckReview", params = dict(
      name = name
    ))
    self._check(wr, r, 'Error starting review for deck with name "%s"', name)
    return r

  def guiExitAnki(self):
    """
    Schedules a request to gracefully close Anki. This operation is asynchronous, so it will return immediately and won't wait until the Anki process actually terminates.

    Sample request:

      client.guiExitAnki()

    Sample result:

      {
        "result": null,
        "error": null
      }
    """
    wr, r = self.send_as_json(action = "guiExitAnki")
    self._check(wr, r, 'Error closing Anki')
    return r
