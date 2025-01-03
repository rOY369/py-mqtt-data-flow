from mqtt_flow.utils.helpers import get_logger
import os


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

            if client.first_time_connected and client.exit_on_reconnect:
                client.disconnect()
                client.loop_stop()
                logger.info(
                    f"MQTT client {client._client_id} reconnected..exiting for clean start"
                )
                os._exit(0)

            client.first_time_connected = True

            logger.info(
                f"MQTT client {client._client_id} connected with result code {rc}"
            )
            logger.info(
                f"{client._client_id} Subscription Topics : {sub_topics}"
            )
            for topic in sub_topics:
                client.subscribe(topic)

        return on_connect
