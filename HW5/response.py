import datetime
import mimetypes
import os
from collections import namedtuple
from typing import Optional, Tuple

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
    def __init__(self):
        self.response = b''
        self._headers = Headers()

    @staticmethod
    def to_serve_request(path, document_root) -> Tuple[int, str, FileDescriber]:
        path = document_root + path
        # HTTP status
        fd = None
        if not os.path.abspath(path).startswith(document_root):
            http_code = FORBIDDEN
        else:
            fd = file_finder(path)
            if fd:
                http_code = OK if fd.can_read else FORBIDDEN
            else:
                http_code = NOT_FOUND
        status_description = http_code_to_description[http_code]
        return http_code, status_description, fd

    def set_header(self, header: dict):
        self._headers.add(header)

    def build_server_headers(self):
        time_now = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        self.set_header({'Date': time_now})
        self.set_header({'Server': "I'm Groot"})
        self.set_header({'Connection': 'keep-alive'})

    def set_status_line(self, http_code, status_description):
        self.response += 'HTTP/1.1 {} {}{}'.format(http_code, status_description, CLRF).encode()

    def prepare(self):
        self.response += self._headers.to_bytes() + CLRF.encode()

    def set_additional_headers(self, fd: FileDescriber, method, path):
        if fd and fd.can_read:
            if fd.content_type:
                self.set_header({'Content-Type': fd.content_type})
                self.set_header({'Content-Length': '{}'.format(fd.length)})
            if method == GET:
                if not ('text' in fd.content_type):
                    # To attach file
                    file_name = path.split('/')[-1]
                    self.set_header({'Content-Disposition': 'attachment; filename={}'.format(file_name)})

    @property
    def content(self) -> bytes:
        return self.response

    @property
    def headers(self) -> dict:
        return self._headers.headers
