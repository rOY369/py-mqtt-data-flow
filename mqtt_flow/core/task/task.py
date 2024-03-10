import abc


class MQTTFlowTask(metaclass=abc.ABCMeta):
    def __init__(self, topic, payload, userdata, task_config):
        self.topic = topic
        self.payload = payload
        self._userdata = userdata
        self.task_config = task_config

        self._client_name = self._userdata.get("_client_name")
        self._tasks_queues = self._userdata.get("_tasks_queues")
        self._clients_queues = self._userdata.get("_clients_queues")

    def publish_message(self, client_name, topic, payload):
        self._clients_queues[client_name]["outgoing"].put(
            {"topic": topic, "payload": payload}
        )

    def execute_task(self, task, task_queue_name):
        task_queue = self._tasks_queues[task_queue_name]
        task_queue.put(task)

    @abc.abstractmethod
    def process(self):
        pass
