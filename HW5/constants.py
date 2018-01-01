OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
NOT_ALLOWED = 405
REQUEST_URI_TOO_LONG = 414
INTERNAL_SERVER_ERROR = 500
http_code_to_description = {OK: 'OK',
                            REQUEST_URI_TOO_LONG: 'Request-URI Too Long',
                            INTERNAL_SERVER_ERROR: 'Internal Server Error',
                            FORBIDDEN: 'FORBIDDEN',
                            NOT_FOUND: 'NotFound',
                            NOT_ALLOWED: 'Method Not Allowed'}
GET = 'GET'
HEAD = 'HEAD'
ALLOWED_METHODS = [GET, HEAD]

MAX_URI_LENGTH = 256  # bytes
CHUNK_SIZE = 1024

CLRF = '\r\n'
