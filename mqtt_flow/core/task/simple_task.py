import abc


class SimpleTask(metaclass=abc.ABCMeta):

    def __init__(self, userdata, task_config):
        self._userdata = userdata
        self.task_config = task_config
        self.name = task_config.get("name")

        self._client_name = self._userdata.get("_client_name")
        self._tasks_queues = self._userdata.get("_tasks_queues")
        self._clients_queues = self._userdata.get("_clients_queues")
        self._tasks = self._userdata.get("_tasks")

    def publish_message(self, client_name, topic, payload):
        self._clients_queues[client_name]["outgoing"].put(
            {"topic": topic, "payload": payload}
        )

    def __str__(self):
        return f"Task {self.name}"

    def submit_task(self, task_name, task_args=None, task_kwargs=None):
        self._tasks[task_name].submit(
            userdata=self._userdata,
            task_args=task_args,
            task_kwargs=task_kwargs,
        )

    @abc.abstractmethod
    def process(self):
        pass
