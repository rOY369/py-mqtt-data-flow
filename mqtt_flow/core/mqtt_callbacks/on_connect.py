from mqtt_flow.utils.helpers import get_logger

logger = get_logger("mqtt_on_connect_callback")


class OnConnectCallback:
    def __init__(self, sub_topics):
        """
        Initializes the OnConnectCallback instance.
        Args:
            sub_topics (list of tuples): A list of topic tuples to subscribe to upon connection.
            Each tuple contains the topic name and the QoS, e.g., [('topic1', 0), ('topic2', 1)].
        """
        self.sub_topics = sub_topics

    @classmethod
    def get_callback(cls, sub_topics):
        """
        Returns the actual on_connect callback function configured with the provided subscription topics.
        Args:
            sub_topics (list of tuples): Subscription topics.
        Returns:
            function: The configured on_connect callback function.
        """
        instance = cls(sub_topics)

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
            for topic, qos in instance.sub_topics:
                client.subscribe(topic, qos)

        return on_connect
