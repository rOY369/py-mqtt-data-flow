import os
from pathlib import Path
import yaml


def find_config_file(filename="mqtt_conf.yml"):
    # Determine the project directory (assuming the current working directory)
    project_dir = Path(os.getcwd())

    # Search for the configuration file in the project directory
    config_path = project_dir / filename
    if config_path.is_file():
        return config_path
    else:
        raise FileNotFoundError(
            f"Configuration file '{filename}' not found in {project_dir}"
        )


def load_config(config_path=None):
    if config_path is None:
        # If no config path is provided, automatically search for it
        config_path = find_config_file()

    # Load the YAML configuration
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    return config


# Example usage
# try:
#     config = load_config()
#     print("Configuration loaded successfully.")
# except FileNotFoundError as e:
#     print(e)
