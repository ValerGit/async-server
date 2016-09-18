import socket
import os
import traceback
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

from coroutine import Future, Task
from parser import parser


def chunk_maker(sequence, chunk_size):
    while sequence:
        yield sequence[:chunk_size]
        sequence = sequence[chunk_size:]


class Server:
    def __init__(self, url, port, num_of_users, num_of_cpu):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.url = url
        self.port = port
        self.num_of_users = num_of_users
        self.num_of_cpu = num_of_cpu
        self.selector = None

    def start(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.url, self.port))
        self.sock.listen(self.num_of_users)
        for _ in range(self.num_of_cpu - 1):
            if not os.fork():
                break
        self.selector = DefaultSelector()
        self.selector.register(self.sock.fileno(), EVENT_READ, self.acceptor)

    def acceptor(self):
        try:
            conn, addr = self.sock.accept()
        except Exception as e:
            # print('here the problem {}'.format(e))
            return
        task = Task(self.handler(), conn)

    def handler(self):
        f = Future()
        conn = yield

        def readable():
            f.set_result(f)

        self.selector.register(conn.fileno(), EVENT_READ, readable)

        yield f

        try:
            self.selector.unregister(conn)
            data = conn.recv(1000)
            response = parser(data.decode('utf-8'), '/Users/iampsg/PycharmProjects/http-test-suite')
        except Exception as e:
            print(traceback.print_tb(e.__traceback__))
            print(e)
            conn.close()

        def writable():
            f.set_result(f)

        self.selector.register(conn, EVENT_WRITE, writable)

        yield f
        self.selector.unregister(conn)

        try:
            for chunk in chunk_maker(response, 1024):
                conn.send(chunk)
                self.selector.register(conn, EVENT_WRITE, writable)
                yield f
                self.selector.unregister(conn)
        finally:
            conn.close()
