# Based on https://gist.github.com/chrisguitarguy/1308286
from typing import Tuple


class InvalidRequest(Exception):
    pass


class Request(object):
    "A simple http request object"

    def __init__(self, raw_request):
        self._raw_request = raw_request


    def parse_request(self)-> Tuple[str, str]:
        "Turn basic request headers in something we can use"
        temp = [i.strip().decode() for i in self._raw_request.splitlines()]

        if -1 == temp[0].find('HTTP'):
            raise InvalidRequest('Incorrect Protocol')

        # Figure out our request method, path, and which version of HTTP we're using
        method, path, _ = [i.strip() for i in temp[0].split()]

        return method, path
