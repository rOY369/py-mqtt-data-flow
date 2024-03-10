from mqtt_flow.core.task.task import MQTTFlowTask


class RelayMessage(MQTTFlowTask):
    def __init__(self, topic, payload, userdata, task_config):
        super().__init__(topic, payload, userdata, task_config)
        self.client_to_publish = self.task_config.get("client_to_publish")
        self.topic_to_publish = self.task_config.get("topic_to_publish")

        if not self.topic_to_publish:
            self.topic_formatter = self.task_config.get("topic_formatter", {})
        else:
            self.topic_formatter = {}

    def format_topic(self):
        if self.topic_to_publish:
            return self.topic_to_publish

        topic = self.topic

        # use topic formatter
        if self.topic_formatter.get("prefix", None):
            topic = f"{self.topic_formatter['prefix']}/{self.topic}"

        if self.topic_formatter.get("suffix", None):
            topic = f"{topic}/{self.topic_formatter['suffix']}"

        # Remove prefix if specified
        remove_prefix = self.topic_formatter.get("remove_prefix")
        if remove_prefix and topic.startswith(remove_prefix):
            # Ensure removal only affects the start
            topic = topic[len(remove_prefix) :].lstrip("/")

        # Remove suffix if specified
        remove_suffix = self.topic_formatter.get("remove_suffix")
        if remove_suffix and topic.endswith(remove_suffix):
            # Ensure removal only affects the end
            topic = topic[: -len(remove_suffix)].rstrip("/")

        return topic

    def format_payload(self):
        return self.payload

    def process(self):
        topic = self.format_topic()
        payload = self.format_payload()
        self.publish_message(self.client_to_publish, topic, payload)
