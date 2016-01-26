import threading
import time
import queue


class ProcessorThread(threading.Thread):
    def __init__(self, processor, data_queue, update_queue, out_queue, done_event):
        super().__init__()
        self.processor = processor
        self.data_queue = data_queue
        self.update_queue = update_queue
        self.out_queue = out_queue
        self.done_event = done_event

    def run(self):
        while not self.done_event.is_set():
            try:
                data = self.data_queue.get_nowait()
                self.processor.process_data(data)
                self.data_queue.task_done()
            except queue.Empty:
                pass

            try:
                # Coalesce updates if we are getting behind
                pending_updates = self.update_queue.qsize()
                if pending_updates > 10:
                    dt = 0
                    for i in range(pending_updates - 3):
                        dt += self.update_queue.get()
                        self.update_queue.task_done()
                else:
                    dt = self.update_queue.get_nowait()
                    self.update_queue.task_done()
                image_ref = self.processor.update(dt)
                if image_ref is not None:
                    self.out_queue.put(image_ref)
            except queue.Empty:
                pass

            time.sleep(0.001)

        print('Ending processor thread')
