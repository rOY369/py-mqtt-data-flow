"""
Library Name: Custom Mqtt
Authors: Dishant
Use case: This library is custom made for iot software. Users can
    create a persistent mqtt client.
Description:
    Users can easily instantiate a custom mqtt object using minimum number
    of parameters. The range of parameters accepted in the form of a
    json makes the mqtt client object configurable.
    The main caveat is that the custom mqtt client object is
    persistent. It makes sense to create such a client by services which
    always require a mqtt connection.
"""

import paho.mqtt.publish as publish_single
import paho.mqtt.client as mqtt
import ssl
import time
from retry import retry
import threading
from queue import Queue
import json
from unittest.mock import Mock

from mqtt_flow.utils.helpers import get_logger
from mqtt_flow.peristence import MockPersistence


class MQTTClient:
    """
    The main interface and entry point for instantiating the custom
    mqtt client object.

    Attributes:
        client (:obj: Mqtt.Client): Standard/Raw mqtt client
            instance. This is only active when the connection is started
            by calling start.
        clientId (str): Unique client id string used when connecting to the
            broker. If not passed in credentials, it will be randomly
            generated by standard mqtt library.
        server (str): The hostname or IP address of the broker. If not
            passed in credentials, it will be set as localhost.
        port (int): Network port of the server host to connect to. Defaults
            to 1883.
        maxMqttReconnectDelay (int): The client will automatically retry
            connection. Between each attempt it will wait a number of
            seconds between 1 and maxMqttReconnectDelay
            seconds. Defaults to 256 seconds.
        willSetTopic (str): Topic that the will message will be
            published to. Defaults to None.
        willSetPayload (str): the message to send as a
            will. Defaults to None.
        keepalive (int): maximum period in seconds allowed between
            communications with the broker. Defaults to 60 seconds.
        certs (dict): certs and info required to connect to aws iot
            broker. All file paths mentioned are string. Iot protocol
            name is used to configure ssl alpn required to connect to aws iot.
            Example:
                {
                    "iotProtocolName": "x-amzn-mqtt-ca",
                    "ca": "<ca file path>",
                    "cert": "<cert file path>",
                    "key": "<key file path>"
                }
        queueSize (int): Items from queue will be published when
            the size reaches this limit. size is in terms of number of items.
            Default : 5
        batchSize (int): Items from batch will be published when
            the size reaches this limit. size is in terms of number of items.
            Default : 5
        publishInterval (int): Time in seconds after which items
            from batch and queue will be published.
            Default : 60
        started(bool): Indicates whether mqtt client connection has been
            initiated or not
    """

    def __init__(
        self,
        client_name=None,
        client_id=None,
        server="127.0.0.1",
        port=1883,
        max_reconnect_delay=8,
        will_set_topic=None,
        will_set_payload=None,
        keep_alive=60,
        queue_size=5,
        batch_size=5,
        publish_interval=60,
        clean_session=True,
        ssl_config=None,
        userdata=None,
        on_connect=Mock(),
        on_message=Mock(),
        on_disconnect=Mock(),
        persistence=None,
    ):
        """
        Sets up the parameters required to setup the mqtt client. It
        does not creates the mqtt client just yet, the user
        needs to call start to create the client and initiate
        the mqtt connection.
        Args:
            on_connect_func_ref (func_ref): Called when the client gets connected
                to broker. The function has to be of the signature -->
                `def on_connect(client, userdata, flags, rc)`
            on_message_func_ref (func_ref): Called when a message has been received
                on a topic that the client subscribes to. The function has
                to be of the signature --> `def on_message(client, userdata, message)`
            on_disconnect_func_ref (func_ref): Called when the client disconnects
                from the broker. The function has to be of
                the signature --> `def on_disconnect(client, userdata, rc)`
            credentials (dict): Settings/Configuration for mqtt client.
                If any of the keys are missing, the default values will be considered.
                Example:
                    {
                        "mqttclientid": "<service_name>",
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
        """
        self.userdata = userdata
        self.client_name = client_name
        self.client_id = client_id
        self.log = get_logger(f"mqtt_client_{client_name}")
        self.server = server
        self.port = port
        self.max_reconnect_delay = max_reconnect_delay
        self.will_topic = will_set_topic
        self.will_payload = will_set_payload
        self.keepalive = keep_alive
        self.ssl_config = ssl_config
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.publish_interval = publish_interval
        self.on_connect = on_connect
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.clean_session = clean_session
        self.batches = {}
        self.queue = Queue(maxsize=self.queue_size)
        self._batch_lock = threading.Lock()
        self.persistence = persistence if persistence else MockPersistence()
        self.started = False
        self.log.info(
            f"Initialising client with name: {client_name} id : {client_id} on {server}:{port} with keepalive={keep_alive} and clean session={clean_session}"
        )

    def _publish_after_interval(self):
        """Publishes from queue and batch at fixed intervals."""
        while self.started:
            self.log.debug("Publishing at interval")
            self._publish_queue()
            self._publish_batches()
            time.sleep(self.publish_interval)

    def _publish_queue(self):
        """Publishes all pending items from the queue."""
        current_queue_size = self.queue.qsize()
        messages = [self.queue.get() for _ in range(current_queue_size)]
        for topic, payload in messages:
            self.publish(topic, payload)

    def _publish_batches(self):
        """Publishes all pending batches."""
        with self._batch_lock:
            for topic, batch in self.batches.items():
                if batch:
                    self.publish(topic, json.dumps(batch))
                    self.batches[topic] = []

    def start(self):
        """Starts the MQTT client connection and background tasks."""
        self.started = True
        threading.Thread(target=self._mqtt_worker).start()
        time.sleep(1)  # Wait for the connection to establish
        threading.Thread(target=self._publish_after_interval).start()
        self.persistence.start(self)

    def stop(self):
        """Stops the MQTT client and finalizes publishing."""
        if hasattr(self, "client"):
            self._publish_batches()
            self._publish_queue()
            self.log.info("Disconnecting MQTT client")
            self.client.disconnect()
            self.started = False

    @retry(
        exceptions=(ConnectionRefusedError, OSError),
        delay=1,
        max_delay=8,
        backoff=2,
    )
    def _retry_connection(self):
        """Retries MQTT connection with exponential backoff."""
        if self.started:
            self.log.info(
                f"Retrying MQTT connection to {self.server}:{self.port}"
            )
            self.client.reconnect()

    def _prepare_ssl_context(self, alpn_protocol, ca, cert, key):
        """Sets up SSL context with ALPN for AWS IoT connection."""
        ssl_context = ssl.create_default_context()
        if alpn_protocol:
            ssl_context.set_alpn_protocols([alpn_protocol])

        if ca:
            ssl_context.load_verify_locations(cafile=ca)

        if cert and key:
            ssl_context.load_cert_chain(certfile=cert, keyfile=key)
        return ssl_context

    def _mqtt_worker(self):
        """Configures and starts the MQTT client."""
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION1,
            client_id=self.client_id,
            userdata=self.userdata,
            clean_session=self.clean_session,
        )
        if self.ssl_config:
            ssl_context = self._prepare_ssl_context(
                self.ssl_config.get("alpn_protocol"),
                self.ssl_config.get("ca"),
                self.ssl_config.get("cert"),
                self.ssl_config.get("key"),
            )
            self.client.tls_set_context(context=ssl_context)
        if self.will_topic and self.will_payload:
            self.client.will_set(self.will_topic, self.will_payload)
        self.client.reconnect_delay_set(
            min_delay=1, max_delay=self.max_reconnect_delay
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        try:
            self.client.connect(self.server, self.port, self.keepalive)
        except (ConnectionRefusedError, OSError):
            self._retry_connection()
        self.client.loop_start()

    def subscribe_topics(self, topics):
        """
        Subscribes the client to a list of topics.

        Args:
            topics (str or list of str): Topic or topics to subscribe to.
        """
        if not hasattr(self, "client"):
            self.log.warning("MQTT client not initialized.")
            return

        if isinstance(topics, str):
            topics = [topics]

        for topic in topics:
            self.client.subscribe(topic)

    def publish(self, topic, payload, persist=False, qos=0):
        """
        Publishes a message immediately to the specified topic.

        Args:
            topic (str): Topic where the message will be published.
            payload (str, int, float): Payload of the message.
        """
        if isinstance(payload, dict) or isinstance(payload, list):
            payload = json.dumps(payload)

        if not hasattr(self, "client"):
            self.log.warning("MQTT client not initialized.")
            return None

        if self.persistence and persist and not self.is_connected():
            self.persistence.append_to_batch(
                {"topic": topic, "payload": payload}
            )
            return None

        if self.is_connected():
            try:
                self.log.debug(
                    f"Outgoing Message from {self.client_name}: {topic} -> {payload}"
                )
                message_info = self.client.publish(topic, payload, qos=qos)
                return message_info
            except OSError as e:
                self.log.warning(f"Failed to publish message: {e}")
                return None
        else:
            return None

    def upload_persisted_batch(self, batch):
        for data_point in batch:
            topic = data_point["topic"]
            payload = data_point["payload"]
            if self.is_connected():
                self.log.info(
                    f"Uploading message from persisted batch to {topic} -> {payload}"
                )
                self.qpublish(topic, payload)
            else:
                return False

        return True

    def qpublish(self, topic, payload):
        """
        Queues a message for publishing. If the queue reaches its size limit,
        messages are published immediately.

        Args:
            topic (str): Topic where the message will be published.
            payload (str, int, float): Payload of the message.
        """
        self.log.debug("Queueing message for publishing.")
        self.queue.put((topic, payload))

        if self.queue.qsize() >= self.queue_size:
            self.log.debug("Queue size limit reached, publishing messages.")
            self._publish_queue()

    def batch_publish(self, topic, payload):
        """
        Adds a message to a batch for a specific topic. When the batch reaches
        its size limit, it is published as a single payload.

        Args:
            topic (str): Topic for the batch.
            payload (str, int, float): Payload to add to the batch.
        """
        with self._batch_lock:
            if topic not in self.batches:
                self.batches[topic] = []

            self.batches[topic].append(payload)

            if len(self.batches[topic]) >= self.batch_size:
                self.log.debug("Batch size limit reached, publishing batch.")
                self.publish(topic, json.dumps(self.batches[topic]))
                self.batches[topic] = []

    def publish_high_priority(self, topic, payload, hostname=None, port=None):
        """
        Publishes a high-priority message without using the persistent client.
        This can be used for immediate, one-off messages.

        Args:
            topic (str): Topic for the message.
            payload (str, int, float): Message payload.
            hostname (str, optional): Hostname of the broker (overrides default).
            port (int, optional): Broker's port (overrides default).
        """
        hostname = hostname or self.server
        port = port or self.port

        try:
            message_info = publish_single.single(
                topic, payload, hostname=hostname, port=port, keepalive=2
            )
            return message_info
        except OSError as e:
            self.log.warning(f"Failed to publish high-priority message: {e}")
            return None

    def is_connected(self):
        """
        Checks if the MQTT client is currently connected to the broker.

        Returns:
            bool: True if the client is connected, False otherwise.
        """
        if hasattr(self, "client"):
            return self.client.is_connected()
        else:
            return False
