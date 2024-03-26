"""IO functions of the project."""

import yaml


def load_yaml_file(file_path):
    """Load a yaml file into memory given a file path."""
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data
