from mqtt_flow.mqtt_lib.mqtt_client import MQTTClient
from mqtt_flow.config.loader import load_config


class MQTTFlow:
    def __init__(self, config_path=None):
        self.config_path = config_path or self._find_default_config()
        self.config = load_config(config_path)
        self.clients = self._create_mqtt_clients()

    def _create_mqtt_clients(self):
        """Create MQTT client instances based on the loaded configuration."""
        clients = {}
        for client_config in self.config.get("mqtt_clients", []):
            client_id = client_config.get("mqttclientid")

            if client_id is None:
                raise ValueError(
                    "Missing 'mqttclientid' in MQTT client configuration"
                )
            
            if client_id in clients:
                raise ValueError(
                    f"Duplicate MQTT client ID found: {client_id}"
                )
            clients[client_id] = MQTTClient(credentials=client_config)
        return clients

    def get_client(self, client_id):
        """Get an MQTT client instance by ID."""
        return self.clients.get(client_id)

    def start_all(self):
        """Start all MQTT client connections."""
        for client in self.clients.values():
            client.start()

    def stop_all(self):
        """Stop all MQTT client connections."""
        for client in self.clients.values():
            client.stop()
