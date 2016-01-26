import threading
import queue


class ConverterThread(threading.Thread):
    def __init__(self, converter, in_queue, out_queue, done_event):
        super().__init__()
        self.converter = converter
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.done_event = done_event

    def run(self):
        while not self.done_event.is_set():
            try:
                add, update, remove, view = self.in_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            output = self.converter.convert(add, update, remove, view)
            self.in_queue.task_done()
            self.out_queue.put(output)

        print('Ending converter thread')
