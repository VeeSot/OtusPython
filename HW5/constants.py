CLRF = '\r\n'
OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
NOT_ALLOWED = 405
REQUEST_URI_TOO_LONG = 414
GET = 'GET'
HEAD = 'HEAD'
ALLOWED_METHODS = [GET, HEAD]

http_code_to_description = {OK: 'OK',
                            REQUEST_URI_TOO_LONG:'Request-URI Too Long',
                            FORBIDDEN: 'FORBIDDEN',
                            NOT_FOUND: 'NotFound',
                            NOT_ALLOWED: 'Method Not Allowed'}
