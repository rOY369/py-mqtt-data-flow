import threading


class TasksExecutor:

    def __init__(self, tasks_queues, queues_config):
        self.tasks_queues = tasks_queues
        self.queues_config = queues_config

    def consume_task_queue(self, task_queue):
        while True:
            task = task_queue.get()
            task.process()

    def start(self):
        for task_queue_name, task_queue in self.tasks_queues.items():

            task_queue_thread = threading.Thread(
                target=self.consume_task_queue, args=(task_queue,)
            )
            task_queue_thread.start()
