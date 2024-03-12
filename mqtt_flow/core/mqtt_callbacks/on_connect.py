from mqtt_flow.utils.helpers import get_logger


class OnConnectCallback:

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

        logger = get_logger("on_connect_mqtt_callback")

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
            logger.info("Sub topics : ", sub_topics)
            for topic in sub_topics:
                logger.info(f"{client._client_id} Subscribing to {topic}")
                client.subscribe(topic)

        return on_connect
