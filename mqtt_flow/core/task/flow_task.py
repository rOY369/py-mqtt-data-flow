from mqtt_flow.core.task.simple_task import SimpleTask


class MQTTFlowTask(SimpleTask):
    def __init__(self, userdata, task_config, topic, payload):
        super().__init__(userdata, task_config)
        self.topic = topic
        self.payload = payload

    def __str__(self):
        return f"Task {self.name} with topic {self.topic} and payload {self.payload}"
