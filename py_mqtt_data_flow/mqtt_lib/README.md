# mqtt_lib

Use this package to create a persistent mqtt client for publish/subscribe.

## Getting Started

**Simple localhost MQTT client without callbacks**

```
from mqtt_lib import MqttCustom

# connect to localhost:1883
mqtt_client = MqttCustom()

mqtt_client.publish("test/topic","payload")

```

**Simple localhost MQTT client with callbacks**

```
from mqtt_lib import MqttCustom

def on_connect(client, userdata, flags, rc):
    # rc: connection return code
    client.subscribe("test/topic")


def on_disconnect(client, userdata, rc):
    # rc: disconnection return code
    pass

def on_message(client, userdata, message):
    topic=message.topic
    payload=message.payload

# connect to localhost:1883
mqtt_client = MqttCustom(on_connect=on_connect,on_message=on_message,on_disconnect=on_disconnect)

mqtt_client.publish("test/topic","payload")
```

## Configuration

Pass `credentials=` keyword argument to tune the connection settings.

```
{
    "mqttclientid": "unique_client_name",
    "mqttserver": "192.168.1.199",
    "mqttport": 9999,
    "maxmqttreconnectdelay": 256,
    "willsettopic": "dummy/will/topic",
    "willsetpayload": "dummy_will_payload",
    "mqttkeepalive": 60,
    "queuesize": 5,
    "batchsize": 5,
    "publishinterval": 60,
    "certs": {
        "iotProtocolName": "x-amzn-mqtt-ca",
        "ca": "<ca file path>",
        "cert": "<cert file path>",
        "key": "<key file path>"
    }
}
```

**Defaults**:

- mqtttclientid : randomly generated
- mqttserver : localhost
- mqttport : 1883
- maxmqttreconnectdelay 256
- willsettopic : ""
- willsetpayload : ""
- mqttkeepalive : 60
- queuesize : 5
- batchsize : 5
- publishinterval : 60
- certs : no ssl/tls by default

## Batch Publish

```
from mqtt_lib import MqttCustom

# connect to localhost:1883
mqtt_client = MqttCustom()

mqtt_client.batch_publish("test/topic","payload")
mqtt_client.batch_publish("test/topic","payload")
mqtt_client.batch_publish("test/topic","payload")
mqtt_client.batch_publish("test/topic","payload")
mqtt_client.batch_publish("test/topic","payload")

```

This will publish the following batch to topic `test/topic`

```
["payload","payload","payload","payload","payload"]
```

- Batches are maintained corresponding to each individual topic.
- `batch_publish(topic,payload)` will append the payload to the batch (list) which corresponds to the provided topic.
- There are 2 cases in which a batch will be published:
  - When batch size reaches the `batchsize` as provided in the configuration.
  - Pending items from all batches will be published after fixed `publishinterval` as provided in the configuration.

## Queue Publish

```
from mqtt_lib import MqttCustom

# connect to localhost:1883
mqtt_client = MqttCustom()

mqtt_client.qpublish("test/topic","payload")
mqtt_client.qpublish("test/topic","payload")
mqtt_client.qpublish("test/topic","payload")
mqtt_client.qpublish("test/topic","payload")
mqtt_client.qpublish("test/topic","payload")

```

This will publish the payload 5 times as individual messages to the topic `test/topic`

- `qpublish(topic,payload)` will add the msg to a queue.
- Messages from the queue are published when:
  - When queue size reaches the `queuesize` as provided in the configuration.
  - Pending items from queue will be published after fixed `publishinterval` as provided in the configuration.

## Misc

**Subscribe topics**

```
mqtt_client.subscribe_topics(["topic1","topic2"])
```

**Publish without making a persistent client i.e without calling mqtt_client.start()**

```
mqtt_client.publish_high_priority("topic","payload",hostname="localhost",port=1883)
```

**Stopping MQTT client connection**

```
mqtt_client.stop()
```

This will not only disconnect the mqtt client from the broker but also stop other threads.

Note: It might take time upto `publishinterval` for all threads to exit.
