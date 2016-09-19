import os
import socket
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

from coroutine import Future, Task
from parser import parser, SERVER_NAME


def chunk_maker(sequence, chunk_size):
    while sequence:
        yield sequence[:chunk_size]
        sequence = sequence[chunk_size:]


class Server:

    def __init__(self, config, num_of_cpu, root_dir):
        self.host = config.get("server", "host")
        self.num_of_users = config.getint("server", "num_of_users")
        self.num_of_cpu = num_of_cpu
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = config.getint("server", "port")
        self.root_dir = root_dir
        self.receive_size = config.getint("server", "receive_chunk")
        self.send_size = config.getint("server", "send_chunk")
        self.selector = None

    def start(self):
        print("Started {server_name} server at {host}:{port}".format(
            host=self.host, port=self.port, server_name=SERVER_NAME))
        print("Root directory is {root_dir}".format(root_dir=self.root_dir))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.num_of_users)
        for _ in range(self.num_of_cpu - 1):
            if not os.fork():
                break
        self.selector = DefaultSelector()
        self.selector.register(self.sock.fileno(), EVENT_READ, self.acceptor)

    def acceptor(self):
        try:
            conn, addr = self.sock.accept()
        except Exception:
            return
        task = Task(self.handler(), conn)

    def handler(self):
        future = Future()
        response = None
        conn = yield

        def readable():
            future.set_result(future)
        self.selector.register(conn.fileno(), EVENT_READ, readable)
        yield future

        try:
            self.selector.unregister(conn)
            data = conn.recv(self.receive_size)
            response = parser(data.decode('utf-8'), self.root_dir)
        except Exception:
            conn.close()

        def writable():
            future.set_result(future)
        self.selector.register(conn, EVENT_WRITE, writable)
        yield future

        self.selector.unregister(conn)
        try:
            for chunk in chunk_maker(response, self.send_size):
                conn.send(chunk)
                self.selector.register(conn, EVENT_WRITE, writable)
                yield future
                self.selector.unregister(conn)
        finally:
            conn.close()
