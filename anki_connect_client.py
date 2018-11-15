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
