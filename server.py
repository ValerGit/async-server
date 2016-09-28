import os
import socket
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

from coroutine import Future, Task
from parser import parser, DEFAULT_ENCODING, SERVER_NAME


def chunk_maker(sequence, chunk_size):
    while sequence:
        yield sequence[:chunk_size]
        sequence = sequence[chunk_size:]


class Server:
    def __init__(self, config, num_of_cpu, root_dir):
        self.host = config.get('server', 'host')
        self.is_parent = True
        self.num_of_cpu = num_of_cpu
        self.num_of_users = config.getint('server', 'num_of_users')
        self.port = config.getint('server', 'port')
        self.receive_size = config.getint('server', 'receive_chunk')
        self.root_dir = root_dir
        self.selector = None
        self.send_size = config.getint('server', 'send_chunk')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def acceptor(self):
        try:
            conn, address = self.sock.accept()
            Task(self.handler(), conn)
        except Exception:
            return

    def start(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.num_of_users)
        print(
            'Started {server_name} server at {host}:{port} with {num_cpu} workers'
            .format(host=self.host, port=self.port, server_name=SERVER_NAME, num_cpu=self.num_of_cpu))
        print('Root directory is {root_dir}'.format(root_dir=self.root_dir))
        for _ in range(self.num_of_cpu - 1):
            if not os.fork():
                self.is_parent = False
                break
        self.selector = DefaultSelector()
        self.selector.register(self.sock.fileno(), EVENT_READ, self.acceptor)

    def handler(self):
        future = Future()
        response = None
        connection = yield

        def readable():
            future.set_result(future)

        self.selector.register(connection, EVENT_READ, readable)
        yield future

        try:
            self.selector.unregister(connection)
            data = connection.recv(self.receive_size)
            response = parser(data.decode(DEFAULT_ENCODING), self.root_dir)
        except Exception:
            connection.close()

        def writable():
            future.set_result(future)

        self.selector.register(connection, EVENT_WRITE, writable)
        yield future

        self.selector.unregister(connection)
        try:
            for chunk in chunk_maker(response, self.send_size):
                connection.send(chunk)
                self.selector.register(connection, EVENT_WRITE, writable)
                yield future
                self.selector.unregister(connection)
        finally:
            connection.close()

    def stop(self):
        if self.is_parent:
            print('{server_name} server stopped'.format(server_name=SERVER_NAME))
            return
        os._exit(os.EX_OK)
