from mqtt_flow.core.task.task_loader import load_task_class


class Task:
    def __init__(self, mqtt_flow_config, task_name, tasks_queues):
        self.config = mqtt_flow_config
        self.name = task_name
        self.task_config = self.config.get("tasks", {}).get(task_name)
        self.task_config["name"] = task_name
        self.task_class = load_task_class(self.task_config.get("path"))
        self.task_queue_name = self.task_config.get("queue_name")
        self.task_queue = tasks_queues.get(self.task_queue_name)

    def submit(self, userdata=None, task_args=None, task_kwargs=None):
        if task_args is None:
            task_args = tuple()
        if task_kwargs is None:
            task_kwargs = {}

        if userdata is None:
            client_for_userdata = self.task_config.get("client_for_userdata")

            for client_config in self.config.get("mqtt_clients", []):
                if client_config.get("client_name") == client_for_userdata:
                    userdata = client_config.get("userdata")

        task = self.task_class(
            userdata, self.task_config, *task_args, **task_kwargs
        )

        self.task_queue.put(task)
