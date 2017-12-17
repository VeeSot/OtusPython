import unittest

import sys

import os

sys.path.append(os.path.join(os.path.dirname(__file__),  ".."))
from HW3 import api


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


class TestField(unittest.TestCase):


    def test_account_field(self):
        """account ‐ строка, опционально, может быть пустым"""
        pass
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

    def test_phone_field(self):
        """phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым"""
        pass

    def test_email_field(self):
        """email ‐ строка, в которой есть @, опционально, может быть пустым"""
        pass

    def test_first_name_field(self):
        """first_name ‐ строка, опционально, может быть пустым"""
        pass

    def test_birthday_field(self):
        """birthday ‐ дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть
пустым"""
        pass

    def test_gender_field(self):
        """gender ‐ число 0, 1 или 2, опционально, может быть пустым"""
        pass

    def test_client_ids_field(self):
        """client_ids ‐ массив числе, обязательно, не пустое"""
        pass

    def test_date_field(self):
        """date ‐ дата в формате DD.MM.YYYY, опционально, может быть пустым"""
        pass




if __name__ == "__main__":
    unittest.main()
