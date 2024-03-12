import os
from pathlib import Path
import yaml
import uuid
import re


class MQTTConfigLoader:
    DEFAULT_CONFIG_FILE_NAME = "mqtt_conf.yml"

    def __init__(
        self,
        config_path=None,
        userdata=None,
        sub_topics=None,
        custom_vars=None,
        persistence=None,
    ):
        if custom_vars is None:
            custom_vars = {}
        self.custom_vars = custom_vars
        self.config = self._load_raw_config(config_path)

        # TODO : add validator
        for client_config in self.config.get("mqtt_clients", []):
            if not client_config.get("client_id"):
                client_config["client_id"] = client_config["client_name"]

        if userdata:
            for client_name, client_userdata in userdata.items():
                self.register_userdata(client_name, client_userdata)
        if sub_topics:
            for client_name, client_sub_topics in sub_topics.items():
                self.register_sub_topics(client_name, client_sub_topics)
        if persistence:
            for client_name, client_persistence in persistence.items():
                self.register_persistence(client_name, client_persistence)

        self.make_client_id_unique()

    @classmethod
    def get_config(
        cls,
        config_path=None,
        userdata=None,
        sub_topics=None,
        custom_vars=None,
        persistence=None,
    ):
        loader = cls(
            config_path=config_path,
            userdata=userdata,
            sub_topics=sub_topics,
            custom_vars=custom_vars,
            persistence=persistence,
        )

        config = loader.config
        logging_config = config.get("logging", {})
        cls.default_log_level = logging_config.get("default_level", "INFO")
        cls.loggers = logging_config.get("loggers", {})

        return loader.config

    def register_persistence(self, client_name, persistence):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_name") == client_name:
                client_config["persistence"] = persistence

    def make_client_id_unique(self):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_id_unique", True) is True:
                client_config["client_id"] = (
                    f"{client_config['client_id']}_{str(uuid.uuid4()).split('-')[0]}"
                )

    def register_sub_topics(self, client_name, topics):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_name") == client_name:
                if "sub_topics" not in client_config:
                    client_config["sub_topics"] = []
                client_config["sub_topics"].extend(topics)

    def register_userdata(self, client_name, userdata):
        for client_config in self.config.get("mqtt_clients", []):
            if client_config.get("client_name") == client_name:
                if "userdata" not in client_config:
                    client_config["userdata"] = {}
                client_config["userdata"].update(userdata)

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

        def interpolate_variables(value, variables):
            """Interpolate variable placeholders in the given value with their actual values."""

            # Match placeholders like {VAR_NAME} and replace them with variable values
            def replace(match):
                var_name = match.group(1)
                if var_name not in variables:
                    raise ValueError(f"Unknown variable: {var_name}")

                return variables.get(var_name)

            interpolated_value = re.sub(r"\{(\w+)\}", replace, value)
            return interpolated_value

        def var_constructor(loader, node):
            """Custom constructor for custom variables with support for interpolation."""
            value = loader.construct_scalar(node)
            return interpolate_variables(value, self.custom_vars)

        def env_constructor(loader, node):
            """Custom constructor for environment variables with support for interpolation."""
            value = loader.construct_scalar(node)
            env_vars = {key: os.getenv(key, "") for key in os.environ}
            return interpolate_variables(value, env_vars)

        CustomLoader.add_constructor("!VAR", var_constructor)
        CustomLoader.add_constructor("!ENV", env_constructor)

        if config_path is None:
            # If no config path is provided, automatically search for it
            config_path = self._find_config_file()

        # Load the YAML configuration
        with open(config_path, "r") as file:
            config = yaml.load(file, Loader=CustomLoader)

        return config
