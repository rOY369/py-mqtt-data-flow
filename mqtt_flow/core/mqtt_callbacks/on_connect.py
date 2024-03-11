from mqtt_flow.utils.helpers import get_logger


class OnConnectCallback:
    def __init__(self, sub_topics):
        """
        Initializes the OnConnectCallback instance.
        Args:
            sub_topics (list of tuples): A list of topic tuples to subscribe to upon connection.
            Each tuple contains the topic name and the QoS, e.g., [('topic1', 0), ('topic2', 1)].
        """
        self.sub_topics = sub_topics
        self.logger = get_logger("mqtt_on_connect_callback")

    @classmethod
    def get_callback(cls, sub_topics=None):
        """
        Returns the actual on_connect callback function configured with the provided subscription topics.
        Args:
            sub_topics (list of tuples): Subscription topics.
        Returns:
            function: The configured on_connect callback function.
        """
        if sub_topics is None:
            sub_topics = []

        instance = cls(sub_topics)
        logger = instance.logger

        def on_connect(client, userdata, flags, rc):
            """
            The actual on_connect callback that subscribes to the specified topics.
            Args:
                client: The MQTT client instance.
                userdata: The private user data as set in Client() or userdata_set().
                flags: Response flags sent by the broker.
                rc: The connection result.
            """
            logger.info(
                f"MQTT client {client._client_id} connected with result code {rc}"
            )
            for topic in instance.sub_topics:
                logger.debug(f"{client._client_id} Subscribing to {topic}")
                client.subscribe(topic)

        return on_connect
