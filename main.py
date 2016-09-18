import socket
import os
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE

from server import Server


if __name__ == "__main__":
    serv = Server("127.0.0.1", 8080, 1000, 2)
    serv.start()
    while True:
        events = serv.selector.select()
        for key, mask in events:
            callb = key.data
            callb()
