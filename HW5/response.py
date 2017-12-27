import datetime
import mimetypes
import os
from collections import namedtuple
from typing import Optional

from constants import http_code_to_description, CLRF, ALLOWED_METHODS, OK, NOT_ALLOWED, NOT_FOUND, GET, FORBIDDEN

FileDescriber = namedtuple('file_describer', 'content_type,content,length,can_read')


class Headers:
    def __init__(self):
        self.headers = {}

    def add(self, header: dict):
        self.headers.update(header)

    def to_bytes(self):
        headers = ''
        for k, v in self.headers.items():
            headers += '{}:{}{}'.format(k, v, CLRF)
        return headers.encode()


def file_finder(path) -> Optional[FileDescriber]:
    if os.path.exists(path):
        if path.endswith('/'):  # There is directory
            path += 'index.html'
            if not os.path.exists(path):
                return FileDescriber(None, None, None, False)

        file_postfix = '.' + path.split('.')[-1]
        content_type = mimetypes.types_map.get(file_postfix, '')
        with open(path, 'rb') as fd:
            content = fd.read()
            length = fd.tell()
            return FileDescriber(content_type, content, length, True)
    return None


class Response:
    def __init__(self, method, path,document_root):
        path = document_root + path
        # HTTP status
        fd = None
        if not os.path.abspath(path).startswith(document_root):
            http_code = FORBIDDEN
        elif method in ALLOWED_METHODS:
            fd = file_finder(path)
            if fd:
                http_code = OK if fd.can_read else FORBIDDEN
            else:
                http_code = NOT_FOUND
        else:
            http_code = NOT_ALLOWED
        status_description = http_code_to_description[http_code]
        self.response = 'HTTP/1.1 {} {}{}'.format(http_code, status_description, CLRF).encode()

        # Headers
        if fd and fd.can_read:
            headers = Headers()
            time_now = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
            headers.add({'Date': time_now})
            headers.add({'Content-Length': '{}'.format(fd.length)})
            headers.add({'Server': "I'm Groot"})
            if fd.content_type:
                headers.add({'Content-Type': fd.content_type})
            headers.add({'Connection': 'keep-alive'})

            if method == GET:
                if not ('text' in fd.content_type):
                    # To attach file
                    file_name = path.split('/')[-1]
                    headers.add({'Content-Disposition': 'attachment; filename={}'.format(file_name)})
            self.response += headers.to_bytes()

        self.response += CLRF.encode()

        if method == GET and fd and fd.can_read:
            self.response += fd.content

    @property
    def content(self) -> bytes:
        return self.response
