HOST = ''
PORT = 8080
CLRF = '\r\n'
OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
NOT_ALLOWED = 405
GET = 'GET'
HEAD = 'HEAD'
ALLOWED_METHODS = [GET, HEAD]
http_code_to_description = {OK: 'OK',
                            FORBIDDEN: 'FORBIDDEN',
                            NOT_FOUND: 'NotFound',
                            NOT_ALLOWED: 'Method Not Allowed'}
