from mqtt_flow.mqtt_lib.mqtt_client import MQTTClient
from mqtt_flow.core.mqtt_callbacks import (
    OnConnectCallback,
    OnMessageCallback,
    OnDisconnectCallback,
)


class MQTTFlow:
    def __init__(self, config):
        self.config = config
        self._clients = self._create_mqtt_clients()

    def _create_mqtt_client(self, client_config):
        """Create MQTT client instance based on the loaded configuration."""

        client_attributes = {
            "client_id": client_config.get("client_id"),
            "server": client_config.get("server"),
            "port": client_config.get("port"),
            "max_reconnect_delay": client_config.get("max_reconnect_delay"),
            "will_set_topic": client_config.get("will_set_topic"),
            "will_set_payload": client_config.get("will_set_payload"),
            "keep_alive": client_config.get("keep_alive"),
            "queue_size": client_config.get("queue_size"),
            "batch_size": client_config.get("batch_size"),
            "publish_interval": client_config.get("publish_interval"),
            "ssl_config": client_config.get("ssl_config"),
            "userdata": client_config.get("userdata"),
        }

        return MQTTClient(
            **{
                attr: value
                for attr, value in client_attributes.items()
                if value
            },
            on_connect=OnConnectCallback.get_callback(
                client_config.get("sub_topics")
            ),
            on_message=OnMessageCallback.get_callback(),
            on_disconnect=OnDisconnectCallback.get_callback(),
        )

    def _create_mqtt_clients(self):
        """Create MQTT client instances based on the loaded configuration."""
        clients = {}
        for client_config in self.config.get("mqtt_clients", []):
            client_name = client_config.get("client_name")

            if client_name is None:
                raise ValueError(
                    "Missing 'client_name' in MQTT client configuration"
                )

            if client_name in clients:
                raise ValueError(
                    f"Duplicate MQTT client name found: {client_name}"
                )
            clients[client_name] = self._create_mqtt_client(client_config)
        return clients

    def get_client(self, client_name):
        """Get an MQTT client instance by name."""
        return self._clients.get(client_name)

    def start_all_clients(self):
        """Start all MQTT client connections."""
        for client in self._clients.values():
            client.start()

    def stop_all_clients(self):
        """Stop all MQTT client connections."""
        for client in self._clients.values():
            client.stop()
