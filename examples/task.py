class Task:
    def __init__(self, topic, payload, userdata, task_config):
        pass

    def process(self):
        print(f"processing task - {self.topic} -> {self.payload}")
