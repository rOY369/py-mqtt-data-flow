from mqtt_flow.core.task.flow_task import MQTTFlowTask
from mqtt_flow.utils.helpers import format_topic
from mqtt_flow.utils.helpers import get_logger


class RelayMessage(MQTTFlowTask):
    def __init__(self, topic, payload, userdata, task_config):
        self.logger = get_logger("relay_message")
        super().__init__(topic, payload, userdata, task_config)
        self.client_to_publish = self.task_config.get("client_to_publish")
        self.topic_to_publish = self.task_config.get("topic_to_publish")
        self.persist = self.task_config.get("persist", False)
        self.log = self.task_config.get("log", False)

        if not self.topic_to_publish:
            self.topic_formatters = self.task_config.get(
                "topic_formatters", []
            )
        else:
            self.topic_formatters = []

    def format_payload(self):
        return self.payload

    def process(self):

        topic = (
            format_topic(self.topic, self.topic_formatters)
            if self.topic_to_publish is None
            else self.topic_to_publish
        )
        payload = self.format_payload()
        self.publish_message(
            self.client_to_publish, topic, payload, persist=self.persist
        )

        if self.log:
            self.logger.info(
                f"Message relayed to client {self.client_to_publish}: {topic} -> {payload}"
            )
