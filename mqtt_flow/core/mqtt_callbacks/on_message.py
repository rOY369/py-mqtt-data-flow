from mqtt_flow.utils.helpers import get_logger
import json


class OnMessageCallback:
    @classmethod
    def get_callback(cls):
        """
        Returns the actual on_message callback function.
        Returns:
            function: The configured on_message callback function.
        """
        logger = get_logger("mqtt_on_msg_callback")

        def on_message(client, userdata, message):
            """
            The actual on_message callback function.
            Args:
                client: The MQTT client instance.
                userdata: The private user data as set in Client() or userdata_set().
                msg: The received message.
            """
            topic = message.topic
            try:
                payload = str(message.payload)[2:-1]
                payload = json.loads(payload.replace("'", '"'))
            except json.decoder.JSONDecodeError:
                payload = str(message.payload)[2:-1]

            logger.debug(
                f"MQTT client {client._client_id} received message on topic {topic} with payload {payload}"
            )

            message = {
                "topic": topic,
                "payload": payload,
                "userdata": userdata,
            }

            userdata["_clients_queues"][userdata["_client_name"]][
                "incoming"
            ].put(message)

        return on_message
