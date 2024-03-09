class Task:
    def __init__(self, message, task_config):
        self.message = message
        self.task_config = task_config

    def process(self):
        print(
            f"processing task - {self.message['topic']} -> {self.message['payload']}"
        )
