#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import inspect
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
from typing import List

from HW3.scoring import get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field:
    def __init__(self, field, value):
        self.field_type = field
        self.value = value


class BaseField(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            field = Field(k, v)
            setattr(self, k, field)
        self.value = None

    def __get__(self, obj, objtype):
        if obj:
            return self.value
        else:
            # Return constrains for fields
            return self

    def __set__(self, obj, value):
        self.value = value


class Validator:
    def __init__(self, obj: dict, schema):
        self.obj = obj
        self.schema = schema
        self.errors = []
        self.__validate()

    @staticmethod
    def check(field, name, obj: dict):
        value = obj.get(name)
        constrains: List[Field] = filter(lambda v: isinstance(v, Field), field.__dict__.values())
        errors = []
        for constrain in constrains:
            if constrain.field_type == 'nullable':
                if not constrain.value:  # Can't be empty
                    if not value:
                        errors.append('Field {} should be filled'.format(name))
            elif constrain.field_type == 'required':
                if constrain.value:
                    if not value:  # Missed in obj
                        errors.append('Field {} should be exists'.format(name))
        return errors

    def __validate(self):
        members = inspect.getmembers(self.schema)
        checked_fields = {x[0]: x[1] for x in members if isinstance(x[1], BaseField)}
        for name, field in checked_fields.items():
            errors = Validator.check(field, name, self.obj)
            self.errors.extend(filter(lambda x: x, errors))

    @property
    def is_valid(self):
        return not self.errors


class CharField(BaseField):
    pass


class ArgumentsField(BaseField):
    pass


class EmailField(CharField):
    pass


class PhoneField(BaseField):
    pass


class DateField(BaseField):
    pass


class BirthDayField(BaseField):
    pass


class GenderField(BaseField):
    pass


class ClientIDsField(BaseField):
    pass


class ClientsInterestsRequest(object):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(object):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(object):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    return response, code


def score_handler(request, ctx, store):
    request_body = request['body']
    if request_body['login'] == ADMIN_LOGIN:
        return {"score": 42}
    arguments = request_body['arguments']
    email = arguments.get('email')
    phone = arguments.get('phone')
    first_name = arguments.get('first_name')
    last_name = arguments.get('last_name')
    gender = arguments.get('gender')
    birthday = arguments.get('birthday')
    enough_information = email and phone or first_name and last_name or gender and birthday

    if enough_information:
        online_score_validator = Validator(request, OnlineScoreRequest)
        if online_score_validator.is_valid:
            score = get_score(store, phone, email, birthday, gender, first_name, last_name)
            response = {"score": score}
            code = OK
        else:
            errors = online_score_validator.errors
            response = {"error": errors[0]}  # We want to notify about only one error]
            code = INVALID_REQUEST
    else:
        response = {"error": "You should to send necessary parameters"}
        code = INVALID_REQUEST

    return response,code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler,
        "online_score": score_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
            request_validator = Validator(request, MethodRequest)
            if not request_validator.is_valid:
                response = request_validator.errors
                code = INVALID_REQUEST
                request = None
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    method = request['method']
                    handler = self.router[method]
                    response, code = handler({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
