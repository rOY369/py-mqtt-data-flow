import re
import importlib
from mqtt_flow.utils.helpers import get_logger

logger = get_logger("mqtt_rule")


class MQTTRule:
    def __init__(self, rule_config):
        """
        Initializes the MQTTRule with the provided configuration.

        Args:
            rule_config (dict): Configuration for the rule, including conditions and task information.
        """
        self.rule_name = rule_config.get("rule_name")
        self.source_client_name = rule_config.get("source_client_name")
        self.regex = rule_config.get("regex")
        self.topic = rule_config.get("topic")
        self.condition = rule_config.get("condition")
        self.task_path = rule_config.get("task")
        self.queue_name = rule_config.get("queue_name")
        self.task_class = self._load_task_class(self.task_path)

    def _load_task_class(self, task_path):
        """
        Dynamically loads the Task class from the given path.

        Args:
            task_path (str): Dot-separated path to the Task class.

        Returns:
            class: The Task class.
        """
        module_name, class_name = task_path.rsplit(".", 1)
        module = importlib.import_module(module_name)

        try:
            class_ = getattr(module, class_name)
        except AttributeError:
            raise ValueError(
                f"Task class {class_name} not found in module {module_name}"
            )

        return class_

    def is_rule_matched(self, message):
        """
        Checks if the given message matches the rule criteria.

        Args:
            message (dict): The message containing 'topic' and 'payload'.

        Returns:
            bool: True if the message matches the rule, False otherwise.
        """
        # Check if the topic matches the regex (if defined)
        if self.regex and not re.match(self.regex, message["topic"]):
            return False

        # Check if the topic exactly matches (if defined)
        if self.topic and self.topic != message["topic"]:
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
                    {"topic": message["topic"], "payload": message["payload"]},
                )
            except Exception as e:
                logger.exception(
                    f"Error evaluating rule condition {self.condition} for {self.rule_name}"
                )
                return False
            if not condition_met:
                return False

        return True
