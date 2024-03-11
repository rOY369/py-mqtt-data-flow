from mqtt_flow.utils.helpers import get_logger


class OnDisconnectCallback:
    @classmethod
    def get_callback(cls):
        """
        Returns the actual on_disconnect callback function.
        Returns:
            function: The configured on_disconnect callback function.
        """
        logger = get_logger("mqtt_on_disconnect_callback")

        def on_disconnect(client, userdata, rc):
            """
            The actual on_disconnect callback function.
            Args:
                client: The MQTT client instance.
                userdata: The private user data as set in Client() or userdata_set().
                rc: The connection result.
            """
            logger.critical(
                f"MQTT client {client._client_id} disconnected with result code {rc}"
            )

        return on_disconnect
