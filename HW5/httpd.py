import socket
from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser

from request import Request
from response import Response


def socket_reader(client_sock)->bytes:
    client_sock.settimeout(1)
    data = b''
    buffer = b''
    try:
        while True:
            data = client_sock.recv(1024)
            buffer += data
    except socket.timeout:
        pass
    except Exception as e:
        print(e)

    return data


def handle_client_connection(client_sock: socket.socket, document_root):
    body = socket_reader(client_sock)
    request = Request(body)
    method, path = request.parse_request()
    path = document_root + path
    response = Response(method, path)
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
        total_workers = opts.workers
        document_root = opts.document_root
        port = opts.port
        address = opts.address
        main(address, port, total_workers, document_root)
    except KeyboardInterrupt:
        print("\nBye-bye...")
        exit(0)
