import datetime
import os
import mimetypes
from collections import namedtuple

from HW5.constants import http_code_to_description, CLRF, ALLOWED_METHODS, OK, NOT_ALLOWED, NOT_FOUND, GET

# FileDescriber = namedtuple('content_type', 'content')

class Headers:
    def __init__(self):
        self.headers = {}

    def add(self, header: dict):
        self.headers.update(header)

    def to_string(self):
        headers = ''
        for k, v in self.headers.items():
            headers += '{}:{}{}'.format(k, v, CLRF)
        return headers


def file_finder(path):

    if os.path.exists(path):

        return True
    return False


class Response:
    def __init__(self, method, path):
        fd = None
        if method in ALLOWED_METHODS:
            fd = file_finder(path)
            if fd:
                http_code = OK
            else:
                http_code = NOT_FOUND
        else:
            http_code = NOT_ALLOWED
        status_description = http_code_to_description[http_code]
        self.response = 'HTTP/1.1 {} {} {}'.format(http_code, status_description, CLRF)

        if fd:
            headers = Headers()
            headers.add({'Content-Length': '42'})
            headers.add({'Date': datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")})
            headers.add({'Server': "I'm Groot"})
            headers.add({'Content-Type': 'text/html'})
            headers.add({'Connection': 'keep-alive'})
            header_string = headers.to_string()

            self.response += header_string

        self.response += CLRF  # Yeah... is necessary

        if method == GET:
            content = '<head><title>It works</title></head><body><h1>Congratulations</h1>'
            self.response += content

    def __bytes__(self):
        return self.response.encode()
