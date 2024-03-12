import importlib


def load_task_class(task_class_path):
    """
    Dynamically loads the Task class from the given path.

    Args:
        task_path (str): Dot-separated path to the Task class.

    Returns:
        class: The Task class.
    """
    if task_class_path:
        module_name, class_name = task_class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)

        try:
            class_ = getattr(module, class_name)
        except AttributeError:
            raise ValueError(
                f"Task class {class_name} not found in module {module_name}"
            )

        return class_

    return None
