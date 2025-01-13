import json
import argparse


class Config:
    """
    This class is responsible for loading a configuration from a JSON file and
    allowing command-line arguments to override specific configuration values.
    """

    def __init__(self, logger, config_path='config/config.json'):
        """
        Initializes the Config class by loading the config from the provided
        JSON file and then overriding specific values with command-line arguments if provided.

        :param config_path: The file path to the configuration JSON file.
        :param logger: Logger.
        """
        self.logger = logger
        self.config = self._load_config(config_path)
        self._override_config_with_cli_args()

    def _load_config(self, config_path):
        """
        Loads the configuration from a JSON file.

        :param config_path: The file path of the JSON configuration file.
        :return: A dict representing the loaded configuration.
        """
        with open(config_path, 'r') as file:
            return json.load(file)

    def _override_config_with_cli_args(self):
        """
        Dynamically parse command-line arguments and override specific values
        in the configuration if those arguments are provided.
        """
        parser = argparse.ArgumentParser(description='Override config values.')

        def add_arguments(prefix, config):
            for key, value in config.items():
                arg_name = f"--{prefix + '.' if prefix else ''}{key}"
                if isinstance(value, dict):
                    add_arguments(f"{prefix + '.' if prefix else ''}{key}", value)
                else:
                    arg_type = type(value)
                    if value is None:
                        arg_type = str
                    parser.add_argument(arg_name, type=arg_type, help=f"Override {prefix}.{key}")

        add_arguments("", self.config)

        args = parser.parse_args()

        def update_config(config, prefix=""):
            for key, value in vars(args).items():
                if value is not None:
                    keys = key.split('.')
                    sub_config = self.config
                    for k in keys[:-1]:
                        sub_config = sub_config.setdefault(k, {})
                    sub_config[keys[-1]] = value

        update_config(self.config)

    def get(self, key, default=None):
        """
        Retrieve a value from the config dict.

        :param key: A string representing the key (dot-separated for nested keys).
        :param default: A default value to return if the key is not found.
        :return: The corresponding value specified in the config, or the default value if not found.
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is default:
                break
        return value

    def validate_config(self):
        """
        Validates the configuration by checking for required fields and their types.

        :return: A tuple of (is_valid, error_messages).
                 is_valid is True if the config is valid, False otherwise.
                 error_messages is a list of errors found during validation.
        """
        errors = []

        required_fields = {
            "data_source": str,
            "neo4j.uri": str,
            "neo4j.username": str,
            "neo4j.password": str,
            "graph_generator": bool,
            "graph_generator_schema_path": str,
            "graph_generator_max_entities": int,
            "graph_generator_min_entities": int,
            "node_type_extraction": str,
            "edge_type_extraction": str,
            "out_dir": str,
            "optional_labels": bool,
            "optional_properties": bool,
            "type_outlier_threshold": int,
            "label_outlier_threshold": int,
            "property_outlier_threshold": int,
            "endpoint_outlier_threshold": int,
            "merge_threshold": float,
            "remove_empty_types": bool,
            "graph_type_name": str,
            "open_labels": bool,
            "open_properties": bool,
            "abstract_type_threshold": float,
            "abstract_type_lookup": bool,
            "max_node_types": int,
            "max_edge_types": int,
            "max_types": bool,
            "validate_graph": bool,
            "merge_schema": bool,
            "schema_to_merge_path": str,
            "schema_merge_threshold": float
        }

        allowed_values = {
            "data_source": ["neo4j"],
            "node_type_extraction": ["label_based", "property_based", "label_property_based"],
            "edge_type_extraction": ["label_based", "property_based", "label_property_based"]
        }

        if self.get("graph_generator_max_entities") < self.get("graph_generator_min_entities"):
            errors.append(f"graph_generator_max_entities has to be greater or equal than graph_generator_min_entities.")

        if self.get("max_types"):
            if self.get("max_node_types") == 0 or self.get("max_edge_types") == 0:
                errors.append("max_node_types and max_edge_types have to be bigger than 0.")

        for field, expected_type in required_fields.items():
            value = self.get(field)

            if value is None:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(value, expected_type):
                errors.append(
                    f"Invalid type for {field}: Expected {expected_type.__name__}, got {type(value).__name__}")

        for field, allowed in allowed_values.items():
            value = self.get(field)
            if value not in allowed:
                errors.append(f"Invalid value for {field}: Expected one of {allowed}, got {value}")

        if errors:
            self.logger.error(errors)
            return False
        else:
            return True
