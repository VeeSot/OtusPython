import os
import sys

import pytest

from HW3.validator import RequestValidator

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from HW3.requests import MethodRequest


@pytest.fixture(scope='function')
def build_request():
    return


# class TestSuite(unittest.TestCase):
#     def setUp(self):
#         self.context = {}
#         self.headers = {}
#         self.store = None
#
#     def get_response(self, request):
#         return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)
#
#     def test_empty_request(self):
#         _, code = self.get_response({})
#         self.assertEqual(api.INVALID_REQUEST, code)

def modifier(action=None, attr=None, value=None):
    def outer(function_to_decorate):
        def inner_function(self):  # аргументы прибывают отсюда
            if action and attr:
                request = self.request_body
                if value:
                    action(request, attr, value)
                else:
                    action(request, attr)
            return function_to_decorate(self)

        return inner_function

    return outer


class MethodRequestFields(object):
    def __init__(self):
        request_body = {"account": "",
                        "login": "",
                        "method": "makePeace",
                        "token": "",
                        "arguments": {}}
        self.request_body = MethodRequest(**request_body)

    # account ‐ строка, опционально, может быть пустым
    @modifier(action=setattr, attr='account', value='Blah')
    def test_account_field_exist_and_filled(self):
        validator = RequestValidator(self.request_body, MethodRequest)
        validator.validate()
        assert validator.is_valid

    def test_login_field(self):
        """login ‐ строка, обязательно, может быть пустым"""
        pass

    def test_method_field(self):
        """method ‐ строка, обязательно, может быть пустым"""
        pass

    def test_token_field(self):
        """token ‐ строка, обязательно, может быть пустым"""
        pass

    def test_arguments_field(self):
        """arguments ‐ словарь (объект в терминах json), обязательно, может быть пустым"""
        pass

#     def test_phone_field(self):
#         """phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым"""
#         pass
#
#     def test_email_field(self):
#         """email ‐ строка, в которой есть @, опционально, может быть пустым"""
#         pass
#
#     def test_first_name_field(self):
#         """first_name ‐ строка, опционально, может быть пустым"""
#         pass
#
#     def test_birthday_field(self):
#         """birthday ‐ дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть
# пустым"""
#         pass
#
#     def test_gender_field(self):
#         """gender ‐ число 0, 1 или 2, опционально, может быть пустым"""
#         pass
#
#     def test_client_ids_field(self):
#         """client_ids ‐ массив числе, обязательно, не пустое"""
#         pass
#
#     def test_date_field(self):
#         """date ‐ дата в формате DD.MM.YYYY, опционально, может быть пустым"""
#         pass


r = MethodRequestFields()
r.test_account_field_exist_and_filled()

if __name__ == "__main__":
    pytest.main()
