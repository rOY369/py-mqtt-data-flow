from mqtt_flow.utils.helpers import get_logger


class OnLogCallback:

    @classmethod
    def get_callback(cls):

        logger = get_logger("on_log_mqtt_callback")

        def on_log(client, userdata, level, buf):
            logger.info(f"client {client._client_id} on_log: {buf}")

        return on_log
