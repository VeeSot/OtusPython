import socket
from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser

from constants import REQUEST_URI_TOO_LONG, http_code_to_description, GET
from request import Request
from response import Response


def socket_reader(client_sock) -> tuple:
    client_sock.settimeout(1)
    data = b''
    max_uri_length = 256  # bytes
    error_code = None
    try:
        # Read first request line with verb and URI
        data += client_sock.recv(1024)
        request_line = data.split()
        uri = request_line[1].strip()  # request_line[0] is HTTP verb,request_line[1] is URI
        if len(uri) > max_uri_length:
            error_code = REQUEST_URI_TOO_LONG
            return data, error_code
        while True:
            buffer = client_sock.recv(1024)
            data += buffer
    except socket.timeout:
        pass
    except Exception as e:
        print(e)

    return data, error_code


def handle_client_connection(client_sock: socket.socket, document_root):
    response = Response()
    response.build_server_headers()

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

    client_sock.send(response.content)
    client_sock.close()


def main(address, port, total_workers, document_root):
    pool = ThreadPoolExecutor(max_workers=total_workers)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((address, port))
    s.listen(5)
    print("\nPress Ctrl+C to shut down server.")
    while True:
        try:
            client_sock, _ = s.accept()
            pool.submit(handle_client_connection, client_sock=client_sock, document_root=document_root)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-a", "--address", action="store", default='')
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-w", "--workers", action="store", default=1)
    op.add_option("-r", "--document_root", action="store", default='/')
    opts, _ = op.parse_args()
    try:
        total_workers = int(opts.workers)
        document_root = opts.document_root
        port = int(opts.port)
        address = opts.address
        main(address, port, total_workers, document_root)
    except KeyboardInterrupt:
        print("\nBye-bye...")
        exit(0)
