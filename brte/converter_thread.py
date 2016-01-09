import threading


class ConverterThread(threading.Thread):
    def __init__(self, converter, in_queue, out_queue):
        super().__init__()
        self.converter = converter
        self.in_queue = in_queue
        self.out_queue = out_queue

    def run(self):
        while True:
            add, update, remove, view = self.in_queue.get()
            output = self.converter.convert(add, update, remove, view)
            self.in_queue.task_done()
            self.out_queue.put(output)
