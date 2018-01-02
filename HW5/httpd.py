import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser

from constants import REQUEST_URI_TOO_LONG, http_code_to_description, MAX_URI_LENGTH, CHUNK_SIZE, INTERNAL_SERVER_ERROR, \
    ALLOWED_METHODS, NOT_ALLOWED
from request import Request
from response import Response


def socket_reader(client_sock) -> tuple:
    client_sock.settimeout(1)
    data = b''
    request_line = b'(?P<http_verb>[A-Z]{3,7}) (?P<uri>\/.+) HTTP/1.[0,1](\\r)?\\n'
    error_code = None
    # HTTP verb has maximal size equal 7 bytes,
    # URI SHOULD contains max 255 bytes,
    # PROTOCOL+version is 8 symbols
    # [CL]RF is 2 symbols
    # 2 symbols for spaces
    max_request_length = 274
    # Read first request line with verb and URI
    data += client_sock.recv(max_request_length)
    match = re.search(request_line, data)
    if match:
        uri = match.group('uri')
        http_verb = match.group('http_verb').decode()
        if not (http_verb in ALLOWED_METHODS):
            return data, NOT_ALLOWED
    else:
        raise Exception("Request {} is incorrect.".format(data.decode()))

    try:
        if len(uri) > MAX_URI_LENGTH:
            error_code = REQUEST_URI_TOO_LONG
            return data, error_code
        while True:
            buffer = client_sock.recv(CHUNK_SIZE)
            data += buffer
    except socket.timeout:
        pass

    return data, error_code


def handle_client_connection(client_sock: socket.socket, document_root):
    response = Response()
    response.build_server_headers()

    try:
        body, error_code = socket_reader(client_sock)
        if error_code:
            status_description = http_code_to_description[error_code]
            response.set_status_line(error_code, status_description)
            response.set_header({'Content-Type': 'text/html'})
            response.set_header({'Content-Length': 0})
            response.prepare()
        else:
            request = Request(body)
            method, path = request.parse_request()
            http_code, status_description, fd = response.to_serve_request(path, document_root)
            response.set_status_line(http_code, status_description)
            response.set_additional_headers(fd, method, path)
            response.prepare()
            if fd and fd.content:
                response.response += fd.content
    except Exception as e:
        logging.exception(e, exc_info=True)
        error_code = INTERNAL_SERVER_ERROR
        status_description = http_code_to_description[error_code]

        message = b'<h1>Ooops, something going wrong!</h1>Please call 911 and wait for help.'

        response.set_status_line(error_code, status_description)
        response.set_header({'Content-Type': 'text/html'})
        response.set_header({'Content-Length': len(message)})
        response.prepare()
        response.response += message
    finally:
        client_sock.sendall(response.content)
        client_sock.close()


def main(address, port, total_workers, document_root):
    pool = ThreadPoolExecutor(max_workers=total_workers)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((address, port))
    s.listen(5)
    logging.info('Server was started')
    print("\nPress Ctrl+C to shut down server.")
    while True:
        try:
            client_sock, (address, port), = s.accept()
            logging.info('Connection on {} port'.format(port))
            pool.submit(handle_client_connection, client_sock=client_sock, document_root=document_root)
        except socket.error as e:
            logging.exception(e, exc_info=True)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-a", "--address", action="store", default='')
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-w", "--workers", action="store", default=1)
    op.add_option("-r", "--document_root", action="store", default='/')
    opts, _ = op.parse_args()
    try:
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname).1s %(message)s',
                            datefmt='%Y.%m.%d %H:%M:%S')
        total_workers = int(opts.workers)
        document_root = opts.document_root
        port = int(opts.port)
        address = opts.address
        main(address, port, total_workers, document_root)
    except KeyboardInterrupt:
        logging.info('Server was stopped')
        print("\nBye-bye...")
        exit(0)
    except Exception as e:
        logging.exception(e, exc_info=True)
