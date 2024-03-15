import logging
import re
from mqtt_flow.config.loader import MQTTConfigLoader

global LOGGER
LOGGER = None


def set_logger(logger):
    global LOGGER
    LOGGER = logger


def get_logger(name, level=None):
    global LOGGER

    if LOGGER:
        return LOGGER
    else:
        loggers = MQTTConfigLoader.loggers
        default_log_level = MQTTConfigLoader.default_log_level

        if not level:
            if name in loggers and "level" in loggers[name]:
                level = loggers[name]["level"]
            else:
                level = default_log_level

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger = logging.getLogger(name)
        logger.setLevel(level)
        return logger


def format_topic(topic, topic_formatters=None):

    if topic_formatters is None:
        return topic

    for topic_formatter in topic_formatters:
        # use topic formatter

        remove_prefix = topic_formatter.get("remove_prefix")
        remove_suffix = topic_formatter.get("remove_suffix")

        if topic_formatter.get("prefix", None):
            topic = f"{topic_formatter['prefix']}/{topic}"

        elif topic_formatter.get("suffix", None):
            topic = f"{topic}/{topic_formatter['suffix']}"

        elif remove_prefix and topic.startswith(remove_prefix):
            # Ensure removal only affects the start
            topic = topic[len(remove_prefix) :].lstrip("/")

        elif remove_suffix and topic.endswith(remove_suffix):
            # Ensure removal only affects the end
            topic = topic[: -len(remove_suffix)].rstrip("/")

    return topic


def match_topic(source_topic, regex=None, rule_topic=None):

    if regex and not re.match(regex, source_topic):
        return False

    if rule_topic and rule_topic != source_topic:
        return False

    return True
