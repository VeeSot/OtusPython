# Based on https://gist.github.com/chrisguitarguy/1308286
from typing import Tuple
from urllib.parse import unquote, urlparse


class Request(object):
    """"A simple http request object"""

    def __init__(self, raw_request):
        self._raw_request = raw_request

    def parse_request(self) -> Tuple[str, str]:
        temp = [i.strip().decode() for i in self._raw_request.split(b'\n')]

        request = temp[0].split()
        method, path, _ = [i.strip() for i in request]

        # Cleans path
        path = urlparse(path).path
        path = unquote(path)

        return method, path
