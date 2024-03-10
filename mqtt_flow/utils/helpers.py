import logging
import re


def get_logger(name, level=logging.INFO):

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
        if topic_formatter.get("prefix", None):
            topic = f"{topic_formatter['prefix']}/{topic}"

        if topic_formatter.get("suffix", None):
            topic = f"{topic}/{topic_formatter['suffix']}"

        # Remove prefix if specified
        remove_prefix = topic_formatter.get("remove_prefix")
        if remove_prefix and topic.startswith(remove_prefix):
            # Ensure removal only affects the start
            topic = topic[len(remove_prefix) :].lstrip("/")

        # Remove suffix if specified
        remove_suffix = topic_formatter.get("remove_suffix")
        if remove_suffix and topic.endswith(remove_suffix):
            # Ensure removal only affects the end
            topic = topic[: -len(remove_suffix)].rstrip("/")

    return topic


def match_topic(original_topic, regex=None, topic=None):

    if regex and not re.match(regex, topic):
        return False

    if topic and original_topic != topic:
        return False

    return True
