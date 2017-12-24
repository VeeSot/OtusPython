import os
import socket

import sys
from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser, Values

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from HW5.constants import HOST, PORT
from HW5.request import Request
from HW5.response import Response


def handle_client_connection(client_sock: socket.socket, document_root):
    body = client_sock.recv(1024)
    request = Request(body)
    method, path = request.parse_request()
    if path.endswith('/'):  # There is directory
        path += 'index.html'
    path = document_root + path
    response = Response(method, path)
    client_sock.send(response.content)
    client_sock.close()


def main(opts: Values):
    total_workers = int(getattr(opts, 'workers'))
    document_root = getattr(opts, 'document_root')
    pool = ThreadPoolExecutor(max_workers=total_workers)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(total_workers)
    print("\nPress Ctrl+C to shut down server.")
    while True:
        try:
            client_sock, _ = s.accept()
            pool.submit(handle_client_connection, client_sock=client_sock, document_root=document_root)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-w", "--workers", action="store", default=1)
    op.add_option("-r", "--document_root", action="store", default='/')
    opts, _ = op.parse_args()
    try:
        main(opts)
    except KeyboardInterrupt:
        print("\nBye-bye...")
        exit(0)
