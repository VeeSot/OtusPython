import logging
import socket
from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser

from constants import REQUEST_URI_TOO_LONG, http_code_to_description, MAX_URI_LENGTH, CHUNK_SIZE, INTERNAL_SERVER_ERROR
from request import Request
from response import Response


def socket_reader(client_sock) -> tuple:
    client_sock.settimeout(1)
    data = b''

    error_code = None
    try:
        # Read first request line with verb and URI
        data += client_sock.recv(CHUNK_SIZE)
        request_line = data.split()
        uri = request_line[1].strip()  # request_line[0] is HTTP verb,request_line[1] is URI
        if len(uri) > MAX_URI_LENGTH:
            error_code = REQUEST_URI_TOO_LONG
            return data, error_code
        while True:
            buffer = client_sock.recv(CHUNK_SIZE)
            data += buffer
    except socket.timeout:
        pass

    return data, error_code


def write_to_socket(client_sock, data):
    length_of_content = len(data)
    i = 0
    while i < length_of_content:
        chunk = data[i:i + CHUNK_SIZE]
        bytes_sent = client_sock.send(chunk)
        i += bytes_sent


def handle_client_connection(client_sock: socket.socket, document_root):
    response = Response()
    response.build_server_headers()

    try:
        body, error_code = socket_reader(client_sock)
        if error_code:
            status_description = http_code_to_description[error_code]
            response.set_status_line(error_code, status_description)
            response.prepare()
        else:
            request = Request(body)
            method, path = request.parse_request()
            http_code, status_description, fd = response.to_serve_request(method, path, document_root)
            response.set_status_line(http_code, status_description)
            response.set_additional_headers(fd, method, path)
            response.prepare()
            if fd and fd.content:
                response.response += fd.content

        write_to_socket(client_sock, response.content)
        client_sock.close()
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
        write_to_socket(client_sock, response.content)
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
            logging.info('Connection on {}'.format(port))
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
