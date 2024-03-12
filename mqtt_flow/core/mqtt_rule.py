from mqtt_flow.utils.helpers import get_logger
from mqtt_flow.utils.helpers import match_topic


class MQTTRule:
    def __init__(self, rule_config):
        """
        Initializes the MQTTRule with the provided configuration.

        Args:
            rule_config (dict): Configuration for the rule, including conditions and task information.
        """
        self.logger = get_logger("mqtt_rule")
        self.rule_name = rule_config.get("rule_name")
        self.source_client_name = rule_config.get("source_client_name")
        self.regex = rule_config.get("regex")
        self.topic = rule_config.get("topic")
        self.condition = rule_config.get("condition")
        self.task_config = rule_config.get("task")
        self.queue_name = self.task_config.get("queue_name")

    def is_rule_matched(self, topic, payload):
        """
        Checks if the given message matches the rule criteria.

        Args:
            message (dict): The message containing 'topic' and 'payload'.

        Returns:
            bool: True if the message matches the rule, False otherwise.
        """

        if not match_topic(topic, self.regex, self.topic):
            return False

        # Evaluate the condition (if defined)
        if self.condition:
            # Safe eval or a similar secure evaluation method should be used here
            # This example uses direct eval for simplicity, which is not secure!
            # Consider using a library like 'safe_eval' for safely evaluating conditions.
            try:
                condition_met = eval(
                    self.condition,
                    {},
                    {"topic": topic, "payload": payload},
                )
            except Exception as e:
                self.logger.exception(
                    f"Error evaluating rule condition {self.condition} for {self.rule_name}"
                )
                return False
            if not condition_met:
                return False

        return True
