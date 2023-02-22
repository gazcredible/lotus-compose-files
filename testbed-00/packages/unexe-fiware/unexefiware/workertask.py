import threading
import time

class WorkerTask:
    def __init__(self):
        self.instance_count = 0
        self.debug_mode = False

    def doWork(self, function, arguments):
        self.start_task()
        update_thread = threading.Thread(target=function, args=(arguments,))
        update_thread.start()

    def start_task(self):
        self.instance_count += 1

    def finish_task(self):
        self.instance_count -= 1

    def isFinished(self):
        return self.instance_count == 0

    def wait_to_finish(self):
        while self.isFinished() == False:
            time.sleep(0.1)

    def onFinish(self):
        self.wait_to_finish()
