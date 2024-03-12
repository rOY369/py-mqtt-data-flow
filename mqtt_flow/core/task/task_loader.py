import importlib


def load_task_class(task_config):
    """
    Dynamically loads the Task class from the given path.

    Args:
        task_path (str): Dot-separated path to the Task class.

    Returns:
        class: The Task class.
    """
    task_path = task_config.get("path")
    if task_path:
        module_name, class_name = task_path.rsplit(".", 1)
        module = importlib.import_module(module_name)

        try:
            class_ = getattr(module, class_name)
        except AttributeError:
            raise ValueError(
                f"Task class {class_name} not found in module {module_name}"
            )

        return class_

    return None
