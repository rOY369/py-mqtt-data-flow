from mqtt_flow.core.task.task import MQTTFlowTask


class RelayMessage(MQTTFlowTask):
    def __init__(self, topic, payload, userdata, task_config):
        super().__init__(topic, payload, userdata, task_config)
        self.client_to_publish = self.task_config.get("client_to_publish")
        self.topic_formatter = self.task_config.get("topic_formatter")

    def format_topic(self):
        # use topic formatter
        return self.topic

    def format_payload(self):
        return self.payload.copy()

    def process(self):
        topic = self.format_topic()
        payload = self.format_payload()
        self.publish_message(self.client_to_publish, topic, payload)
