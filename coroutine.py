class Future:
    def __init__(self):
        self.result = None
        self._callbacks = []

    def append_done_callback(self, func):
        self._callbacks.append(func)

    def set_result(self, result):
        self.result = result
        for func in self._callbacks:
            func(result)


class Task:
    def __init__(self, corout, conn):
        self.corout = corout
        self.corout.send(None)
        self.fileno = conn
        fut = Future()
        fut.set_result(conn)
        self.step(fut)

    def step(self, fut):
        try:
            next_fut = self.corout.send(fut.result)
        except (StopIteration, ValueError):
            return
        next_fut.append_done_callback(self.step)
