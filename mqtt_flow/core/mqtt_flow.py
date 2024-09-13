from mqtt_flow.mqtt_lib.mqtt_client import MQTTClient
from mqtt_flow.core.mqtt_rule import MQTTRule
from mqtt_flow.core.mqtt_callbacks import (
    OnConnectCallback,
    OnMessageCallback,
    OnDisconnectCallback,
)
from mqtt_flow.core.tasks_executor import TasksExecutor
import queue
import threading
from mqtt_flow.core._task import Task
from mqtt_flow.core.task.task_loader import load_task_class
from mqtt_flow.utils.helpers import get_logger
from mqtt_flow.peristence import MQTTPersistence
from mqtt_flow.peristence import PersistenceQueueError
import time

# TODO trigger in persistence (application level)
# TODO config, readme
# TODO code doc + docs link on github


class MQTTFlow:
    PUBLISH_DELAY_IN_SECONDS = 0.005

    def __init__(self, config):

        self.logger = get_logger("mqtt_flow")
        self.config = config
        self._clients_queues = self._create_mqtt_clients_queues()
        self._tasks_queues = self._create_tasks_queues()
        self._rules = self._create_rules()
        self._tasks = self._create_tasks()
        self._register_clients_base_userdata()
        self._clients = self._create_mqtt_clients()
        self._tasks_executor = TasksExecutor(
            self._tasks_queues,
            self.config.copy().get("tasks_queues", []),
            self.config.copy().get("pools", []),
        )

    def _create_tasks(self):
        tasks = {}
        for task_name in self.config.get("tasks", {}):
            tasks[task_name] = Task(self.config, task_name, self._tasks_queues)
        return tasks

    def _create_rules(self):
        rules = {}
        for rule_config in self.config.get("rules", []):
            rule_name = rule_config.get("name")
            source_client_name = rule_config.get("source_client_name")

            if source_client_name not in rules:
                rules[source_client_name] = {}
            rules[source_client_name][rule_name] = MQTTRule(rule_config)
        return rules

    def _register_clients_base_userdata(self):
        for client_config in self.config.get("mqtt_clients", []):

            client_name = client_config.get("client_name")
            if "userdata" not in client_config:
                client_config["userdata"] = {}

            client_config["userdata"]["_client_name"] = client_name
            client_config["userdata"]["_tasks_queues"] = self._tasks_queues
            client_config["userdata"]["_clients_queues"] = self._clients_queues
            client_config["userdata"]["_tasks"] = self._tasks

    def _create_mqtt_clients_queues(self):
        queues = {}
        for client_config in self.config.get("mqtt_clients", []):
            client_name = client_config.get("client_name")
            queues[client_name] = {
                "incoming": queue.Queue(),
                "outgoing": queue.Queue(),
            }
        return queues

    def _create_tasks_queues(self):
        queues = {}
        for queue_config in self.config.get("tasks_queues", []):
            queue_name = queue_config.get("name")
            queue_size = queue_config.get("size")
            queues[queue_name] = queue.Queue(queue_size)
        return queues

    def _create_mqtt_client(self, client_config):
        """Create MQTT client instance based on the loaded configuration."""

        client_attributes = {
            "client_name": client_config.get("client_name"),
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
            "clean_session": client_config.get("clean_session"),
            "on_log_callback_enable": client_config.get(
                "on_log_callback_enable"
            ),
        }

        persistence = client_config.get("persistence")
        if not persistence:
            persistence_config = client_config.get("persistence_config")
            if persistence_config:
                try:
                    persistence = MQTTPersistence(persistence_config)
                except PersistenceQueueError:
                    self.logger.warning(
                        f"Failed to initialise persistence for client {client_config.get('client_name')}"
                    )

        return MQTTClient(
            **{
                attr: value
                for attr, value in client_attributes.items()
                if value is not None
            },
            on_connect=OnConnectCallback.get_callback(
                client_config.get("sub_topics")
            ),
            on_message=OnMessageCallback.get_callback(),
            on_disconnect=OnDisconnectCallback.get_callback(),
            persistence=persistence,
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

    def _incoming_msg_queue_consumer(self, client_name):
        incoming_queue = self._clients_queues[client_name]["incoming"]

        while True:
            try:
                message = incoming_queue.get()
                topic = message["topic"]
                payload = message["payload"]
                userdata = message["userdata"]

                self.logger.debug(
                    f"Incoming Message : {message['topic']} -> {message['payload']}"
                )

                for rule_name, rule in self._rules.get(
                    client_name, {}
                ).items():
                    if rule.is_rule_matched(topic, payload):
                        self.logger.debug(
                            f"Rule {rule_name} matched for {client_name}"
                        )
                        self.logger.debug(
                            f"Client {client_name} Incoming Message : {message['topic']} -> {message['payload']}"
                        )
                        self._tasks[rule.task_name].submit(
                            userdata=userdata, task_args=(topic, payload)
                        )
            except Exception:
                self.logger.exception(
                    "Exception in Incoming Message Queue Consumer"
                )

    def _outgoing_msg_queue_consumer(self, client_name):
        outgoing_queue = self._clients_queues[client_name]["outgoing"]
        client = self._clients[client_name]
        while True:
            try:
                message = outgoing_queue.get()
                self.logger.debug(
                    f"Client {client_name} Outgoing Message : {message['topic']} -> {message['payload']}"
                )
                msg_info = client.publish(
                    message["topic"],
                    message["payload"],
                    *message.get("args", []),
                    **message.get("kwargs", {}),
                )
                if msg_info is not None:
                    self.logger.debug(
                        f"Message sent to topic : {message['topic']} with rc: {msg_info.rc}"
                    )

                # if msg_info is not None:
                #     if msg_info.rc != 0:
                #         self.logger.warning(
                #             f"Failed to publish message to {client_name}: {msg_info.rc}"
                #         )
                # time.sleep(self.PUBLISH_DELAY_IN_SECONDS)
            except Exception:
                self.logger.exception(
                    "Exception in Outgoing Message Queue Consumer"
                )

    def submit_task(self, task_name, task_args=None, task_kwargs=None):
        self._tasks[task_name].submit(
            task_args=task_args, task_kwargs=task_kwargs
        )

    def start(self):
        """Start all MQTT client connections."""
        for client in self._clients.values():
            client.start()

        for client_name in self._clients_queues.keys():
            threading.Thread(
                target=self._incoming_msg_queue_consumer,
                args=(client_name,),
            ).start()
            threading.Thread(
                target=self._outgoing_msg_queue_consumer,
                args=(client_name,),
            ).start()

        self._tasks_executor.start()

    def stop(self):
        """Stop all MQTT client connections."""
        for client in self._clients.values():
            client.stop()
