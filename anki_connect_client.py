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
