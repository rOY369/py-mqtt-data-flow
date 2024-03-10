from mqtt_flow import MQTTFlow
from mqtt_flow import MQTTConfigLoader
import time

mqtt_flow = MQTTFlow(
    MQTTConfigLoader.get_config(
        config_path="/home/roymiller/workspace/my-craft/py-mqtt-data-flow/examples/config.yml"
    )
)
mqtt_flow.start()

client1 = mqtt_flow.get_client("client1")
client2 = mqtt_flow.get_client("client2")


# client1.publish("test/topic2", "hello")
for i in range(100):
    client1.publish("test/topic1", f"hello{i}")
    time.sleep(1)
