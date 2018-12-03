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
    TODO
    """
    response, result = self.send_as_json(action = "storeMediaFile", params = dict(
      filename = filename,
      data = data,
    ))
    self._check(response, result,
      'Error storing media file "%s"', filename
    )
    return result

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
