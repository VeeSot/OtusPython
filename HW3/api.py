#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser

from HW3.constants import INVALID_REQUEST, OK, MEANING_OF_LIFE, ADMIN_LOGIN, BAD_REQUEST, INTERNAL_ERROR, NOT_FOUND, \
    ERRORS, ADMIN_SALT, SALT

# sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from HW3.requests import ClientsInterestsRequest, OnlineScoreRequest, MethodRequest
from HW3.scoring import get_score, get_interests
from HW3.validator import Validator


class ShutDownException(Exception):
    pass


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def clients_interests(request, ctx: dict, store):
    arguments = request['body']['arguments']

    clients_interests_request_validator = Validator(arguments, ClientsInterestsRequest)
    if clients_interests_request_validator.is_valid:
        ids = arguments['client_ids']
        response = {idx: get_interests(store=store, cid=idx) for idx in ids}
        code = OK
        ctx.update({'nclients': len(ids)})
    else:
        errors = clients_interests_request_validator.errors
        response = {"error": errors[0]}
        code = INVALID_REQUEST

    return response, code, ctx


def method_handler(request, ctx, store):
    method = request['body']['method']
    middleware = {
        "clients_interests": clients_interests,
        "online_score": score_handler,
        "shutdown": score_handler
    }
    handler = middleware[method]
    return handler(request, ctx, store)


def shoutdown(*args, **kwargs):
    raise ShutDownException


def score_handler(request, ctx: dict, store):
    request_body = request['body']
    arguments = request_body['arguments']
    email = arguments.get('email')
    phone = arguments.get('phone')
    first_name = arguments.get('first_name')
    last_name = arguments.get('last_name')
    gender = arguments.get('gender')
    birthday = arguments.get('birthday')
    enough_information = bool(email and phone) or bool(first_name and last_name) or bool(gender and birthday)

    if enough_information:
        online_score_validator = Validator(request, OnlineScoreRequest)
        filled_fields = online_score_validator.filled_fields
        ctx.update({'has': filled_fields})
        if online_score_validator.is_valid:
            if request_body['login'] == ADMIN_LOGIN:
                response = {"score": MEANING_OF_LIFE}
            else:
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

    return response, code, ctx


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler,
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
                    handler = self.router[path]
                    response, code, context = handler({"body": request, "headers": self.headers}, context, self.store)
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
        self.wfile.write(json.dumps(r).encode())
        return


def runner():
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
    except ShutDownException:
        logging.info("Bye-Bye")
    server.server_close()


if __name__ == "__main__":
    runner()
