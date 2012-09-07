import logging
import Queue
import threading
import time

TIMEOUT_SECS = 30
STATUS_SECS = 30

DONE = False

WORK_Q = Queue.Queue()
COMPLETE_Q = Queue.Queue()
FAILED_Q = Queue.Queue()
SKIPPED_Q = Queue.Queue()

"""
Print out a status message so users don't wonder if stuff is still
happening or not
"""
class StatusThread(threading.Thread):
    def run(self):
        log = logging.getLogger(__name__)
        while not DONE:
            log.info('Still deploying applications and data...')
            time.sleep(STATUS_SECS)


"""
Get work from the work queue and execute the deploy method. All tasks in the
WORK_Q must contain a deploy method 
"""
class WorkerThread(threading.Thread):
    def run(self):
        log = logging.getLogger(__name__)
        while not DONE:
            try:
                task = WORK_Q.get(True, timeout=TIMEOUT_SECS)
            except:
                task = None
            if task:
                rc = task.deploy()
                if rc == 0:
                    log.info('Deploy of %s succeeded.' % task.name)
                    task.success = True
                    task.complete = True
                    COMPLETE_Q.put(task)
                elif rc == -1:
                    log.info('Deploy of %s skipped.' % task.name)
                    task.success = True
                    task.complete = True
                    SKIPPED_Q.put(task)
                else:
                    log.error('Deploy of %s failed.' % task.name)
                    task.success = False
                    task.complete = True
                    FAILED_Q.put(task)
                WORK_Q.task_done()
