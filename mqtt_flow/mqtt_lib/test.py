from mqtt_lib import MqttCustom
from iot_logging import get_logger
import time
import logging


credentials = {
    "queuesize": 2,
    "batchsize": 2,
    "publishinterval": 10,
    "mqttclientid": "hahaha",
}

mqtt_client = MqttCustom(
    credentials=credentials,
    log_level=logging.DEBUG,
)
mqtt_client.start()

print(mqtt_client.client._client_id)
print(mqtt_client.client._connect_properties)
log = get_logger(
    "mqtttest", controller_id="Test123", site_id="Test123", level=logging.DEBUG
)

log.info("publishing in queue")
mqtt_client.qpublish("test", "hello")
mqtt_client.qpublish("test", "hello")
mqtt_client.qpublish("test", "hello")


mqtt_client.batch_publish("test", "batchhello")
mqtt_client.batch_publish("test", "batchhello")
mqtt_client.batch_publish("test", "batchhello")
mqtt_client.batch_publish("test", "batchhello")
mqtt_client.batch_publish("test", "batchhello")

mqtt_client.stop()
