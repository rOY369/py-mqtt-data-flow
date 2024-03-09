from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
import threading
import uuid
from mqtt_flow.utils.helpers import get_logger

logger = get_logger("executor_pools")


class SequentialPool:
    def __init__(self, pool_config):
        self.name = pool_config.get("name")
        self.max_workers = pool_config.get("max_workers")

    @property
    def resource_available(self):
        return True

    @property
    def running_tasks_count(self):
        return 0

    def submit(self, task, *args, **kwargs):
        kwargs.pop("error_callback", None)
        try:
            task(*args, **kwargs)
        except Exception:
            logger.exception("Exception in Task Consumer")


class SimpleThreadPool:
    TASK_THREAD_NAME = "flow_task"

    def __init__(self, pool_config):
        self.name = pool_config.get("name")
        self.max_workers = pool_config.get("max_workers")

    @property
    def resource_available(self):
        return self.running_tasks_count <= self.max_workers

    @property
    def running_tasks_count(self):
        all_threads = threading.enumerate()
        metric_task_threads = [
            thread
            for thread in all_threads
            if thread.name.startswith(self.TASK_THREAD_NAME)
        ]
        return len(metric_task_threads)

    def submit(self, task, *args, **kwargs):
        kwargs.pop("error_callback", None)

        threading.Thread(
            target=task,
            args=args,
            kwargs=kwargs,
            name=f"{self.TASK_THREAD_NAME}_{uuid.uuid4()}",
        ).start()


class ThreadPool:
    def __init__(self, pool_config):
        self.name = pool_config.get("name")
        self.max_workers = pool_config.get("max_workers")

    @property
    def resource_available(self):
        return True

    @property
    def running_tasks_count(self):
        return self._pool._work_queue.qsize()

    def submit(self, task, *args, **kwargs):
        kwargs.pop("error_callback", None)

        return self._pool.submit(task, *args, **kwargs)


class ProcessPool:
    def __init__(self, pool_config):
        self.name = pool_config.get("name")
        self.max_workers = pool_config.get("max_workers")

    @property
    def resource_available(self):
        return True

    @property
    def running_tasks_count(self):
        return 0

    def submit(self, task, *args, **kwargs):
        return self.pool.apply_async(task, args=args, **kwargs)
