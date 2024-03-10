from mqtt_flow.peristence import Persistence
from mqtt_flow.utils.helpers import match_topic, format_topic
import re


class MQTTPersistence(Persistence):

    def __init__(self, config):
        super().__init__(config)
        self._rules = config.get("rules", [])

    def apply_rule(self, topic):
        for rule in self._rules:
            topic_regex = rule.get("regex")
            filter_topic = rule.get("topic")
            reupload_topic_formatters = rule.get(
                "reupload_topic_formatters", []
            )

            if match_topic(topic, topic_regex, filter_topic):
                reupload_topic = format_topic(topic, reupload_topic_formatters)
                return reupload_topic

        return None

    def format_payload(self, payload):
        return payload

    def append_to_batch(self, data_point):
        topic = data_point["topic"]
        payload = data_point["payload"]

        reupload_topic = self.apply_rule(topic)

        if reupload_topic:
            reupload_payload = self.format_payload(payload)
            reupload_data_point = {
                "topic": reupload_topic,
                "payload": reupload_payload,
            }

            super().append_to_batch(reupload_data_point)
