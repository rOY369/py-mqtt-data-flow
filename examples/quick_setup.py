from mqtt_flow import MQTTFlow

mqtt_flow = MQTTFlow(
    config_path="/home/roymiller/workspace/my-craft/py-mqtt-data-flow/examples/config.yml"
)
mqtt_flow.start_all()