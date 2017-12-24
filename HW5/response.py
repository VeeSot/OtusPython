import datetime
import mimetypes
import os
from collections import namedtuple
from typing import Optional

from HW5.constants import http_code_to_description, CLRF, ALLOWED_METHODS, OK, NOT_ALLOWED, NOT_FOUND, GET

FileDescriber = namedtuple('file_describer', 'content_type,content,length')


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
        file_postfix = '.' + path.split('.')[-1]
        content_type = mimetypes.types_map.get(file_postfix, '')
        with open(path, 'rb') as fd:
            content = fd.read()
            length = fd.tell()
            file_describer = FileDescriber(content_type, content, length)
        return file_describer
    return None


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
        self.response = 'HTTP/1.1 {} {} {}'.format(http_code, status_description, CLRF).encode()

        if fd:
            headers = Headers()
            time_now = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
            headers.add({'Date': time_now})
            headers.add({'Content-Length': '{}'.format(fd.length)})
            headers.add({'Server': "I'm Groot"})
            if fd.content_type:
                headers.add({'Content-Type': fd.content_type})
            headers.add({'Connection': 'close'})
            self.response += headers.to_bytes()

        if fd and method == GET:
            if not('text' in fd.content_type):
                file_name = path.split('/')[-1]
                headers = Headers()
                headers.add({'Content-Disposition': 'attachment; filename={}'.format(file_name)})
                self.response += headers.to_bytes()
            self.response += CLRF.encode()
            self.response += fd.content
    @property
    def content(self)->bytes:
        return self.response
