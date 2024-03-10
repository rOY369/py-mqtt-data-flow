import os
from pathlib import Path
import yaml
import uuid


class MQTTConfigLoader:
    DEFAULT_CONFIG_FILE_NAME = "mqtt_conf.yml"

    def __init__(
        self,
        config_path=None,
        client_id_suffix=None,
        userdata=None,
        sub_topics=None,
        custom_vars=None,
    ):
        self.config = self._load_raw_config(config_path)

        if custom_vars is None:
            custom_vars = {}
        self.custom_vars = custom_vars

        # TODO : add validator
        for client_config in self.config.get("mqtt_clients", []):
            client_config["client_id"] = client_config["client_name"]

        if client_id_suffix:
            for client_name, suffix in client_id_suffix.items():
                self.add_suffix_to_client_id(client_name, suffix)
        if userdata:
            for client_name, userdata in userdata.items():
                self.register_userdata(client_name, userdata)
        if sub_topics:
            for client_name, sub_topics in sub_topics.items():
                self.register_sub_topics(client_name, sub_topics)

        self.make_client_id_unique()

    @classmethod
    def get_config(
        cls,
        config_path=None,
        client_id_suffix=None,
        userdata=None,
        sub_topics=None,
        custom_vars=None,
    ):
        loader = cls(
            config_path=config_path,
            client_id_suffix=client_id_suffix,
            userdata=userdata,
            sub_topics=sub_topics,
            custom_vars=custom_vars,
        )

        return loader.config

    def make_client_id_unique(self):
        for client_config in self.config.get("mqtt_clients", []):
            client_config["client_id"] = (
                f"{client_config['client_id']}_{str(uuid.uuid4()).split('-')[0]}"
            )

    def add_suffix_to_client_id(self, client_name, suffix):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_name") == client_name:
                client_config["client_id"] = (
                    f"{client_config['client_name']}_{suffix}"
                )

    def append_sub_topics(self, client_name, topics):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_name") == client_name:
                client_config.get("sub_topics", []).extend(topics)

    def register_userdata(self, client_name, userdata_key, userdata_value):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_name") == client_name:
                if "userdata" not in client_config:
                    client_config["userdata"] = {}
                client_config["userdata"][userdata_key] = userdata_value

    def _find_config_file(self, default_file=DEFAULT_CONFIG_FILE_NAME):
        # Determine the project directory (assuming the current working directory)
        project_dir = Path(os.getcwd())

        # Search for the configuration file in the project directory
        config_path = project_dir / default_file
        if config_path.is_file():
            return config_path
        else:
            raise FileNotFoundError(
                f"Configuration file '{default_file}' not found in {project_dir}"
            )

    def _load_raw_config(self, config_path=None):

        class CustomLoader(yaml.SafeLoader):
            pass

        def var_constructor(loader, node):
            """Extracts the custom variable from the node's value."""
            value = loader.construct_scalar(node)
            return self.custom_vars.get(value, f"Undefined variable: {value}")

        def env_constructor(loader, node):
            """Extracts the environment variable from the node's value."""
            value = loader.construct_scalar(node)
            env_var, default_value = value.split(" ", 1)[0], None
            if " " in value:  # Check if there's a default value provided
                env_var, default_value = value.split(" ", 1)
            return os.getenv(env_var.strip("${}"), default_value)

        CustomLoader.add_constructor("!VAR", var_constructor)
        CustomLoader.add_constructor("!ENV", env_constructor)

        if config_path is None:
            # If no config path is provided, automatically search for it
            config_path = self._find_config_file()

        # Load the YAML configuration
        with open(config_path, "r") as file:
            config = yaml.load(file, Loader=CustomLoader)

        return config
