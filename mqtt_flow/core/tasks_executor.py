import threading
from mqtt_flow.core.executor_pools import (
    SimpleThreadPool,
    ThreadPool,
    SequentialPool,
)
from mqtt_flow.utils.helpers import get_logger


class TasksExecutor:
    POOL_TYPES = {
        "simple_thread": SimpleThreadPool,
        "thread": ThreadPool,
        "sequential": SequentialPool,
    }

    def __init__(self, tasks_queues, queues_config, pools_config):
        self.logger = get_logger("tasks_executor")
        self.tasks_queues = tasks_queues
        self.queues_config = queues_config
        self.pools_config = pools_config
        self._pools = self._create_pools()

    def _create_pools(self):
        pools = {}
        for pool_config in self.pools_config:
            pool_name = pool_config.get("name")
            pool_type = pool_config.get("type")
            pools[pool_name] = self.POOL_TYPES[pool_type](pool_config)
        return pools

    def consume_task_queue(self, task_queue, pool):
        while True:
            try:
                task = task_queue.get()
                self.logger.debug(f"Executing Task {task}")
                if pool.resource_available:
                    pool.submit(task.process)
            except Exception:
                self.logger.exception("Exception in Task Consumer")

    def start(self):
        for task_queue_name, task_queue in self.tasks_queues.items():

            for queue_config in self.queues_config:
                if queue_config.get("name") == task_queue_name:
                    pool_name = queue_config.get("pool")
                    pool = self._pools[pool_name]

            task_queue_thread = threading.Thread(
                target=self.consume_task_queue, args=(task_queue, pool)
            )
            task_queue_thread.start()
