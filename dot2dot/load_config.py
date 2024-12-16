"""
This module allows the user to load a
default or a custom configuration from a JSON file.
"""
import json
import os
from jsonschema import validate, ValidationError
from dot2dot.utils import get_base_directory, parse_rgba
from dot2dot.default_scheme_config import DEFAULT_CONFIG_CONTENT, CONFIG_SCHEMA


class LoadConfig:
    """
    This class allows the user to load a default or a custom
    configuration from a JSON file, validating each field and
    replacing corrupted or missing fields with default values.
    """

    def __init__(self,
                 default_config_file='config_default.json',
                 user_config_file='config_user.json'):
        self.default_config_file = default_config_file
        self.user_config_file = user_config_file
        self.config = self.load_and_fix_config()

    def ensure_config_directory_exists(self, config_directory):
        """
        Ensures that the configuration directory exists.
        """
        if not os.path.exists(config_directory):
            os.makedirs(config_directory)
            print(f"Created configuration directory at {config_directory}.")

    def create_default_config(self, config_path):
        """
        Creates a default configuration file.
        """
        try:
            with open(config_path, 'w') as file:
                json.dump(DEFAULT_CONFIG_CONTENT, file, indent=4)
            print(f"Created default configuration at {config_path}.")
            return DEFAULT_CONFIG_CONTENT.copy()
        except Exception as e:
            print(f"Error creating default configuration: {e}")
            return {}

    def validate_config_field(self, key, value):
        """
        Validates a single configuration field against its schema.

        Args:
            key (str): The configuration key.
            value: The value to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        field_schema = CONFIG_SCHEMA['properties'].get(key)
        if not field_schema:
            print(f"No schema defined for key: {key}. Skipping validation.")
            return False  # Unknown field, treat as invalid

        try:
            validate(instance=value, schema=field_schema)
            return True
        except ValidationError as e:
            print(f"Validation failed for key '{key}': {e.message}")
            return False

    def load_and_fix_config(self):
        """
        Loads the configuration file, validates each field, and fixes corrupted fields
        by replacing them with default values. Saves the fixed configuration.

        Returns:
            dict: A valid configuration dictionary.
        """
        base_directory = get_base_directory()
        config_directory = os.path.join(base_directory, 'assets', 'config')
        self.ensure_config_directory_exists(config_directory)

        default_config_path = os.path.join(config_directory,
                                           self.default_config_file)
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        # Attempt to load user config first
        config = {}
        config_file = None
        if os.path.exists(user_config_path):
            config_file = user_config_path
            try:
                with open(config_file, 'r') as file:
                    config = json.load(file)
                print(f"Loaded user configuration from {user_config_path}.")
            except json.JSONDecodeError:
                print(
                    f"User config file {user_config_path} is not valid JSON.")
            except Exception as e:
                print(
                    f"Error loading user config file {user_config_path}: {e}")
        is_config_valid = self.validate_config(config)
        if config and is_config_valid:
            return config
        # If user config is invalid or not present, attempt to load default config
        if not config or not is_config_valid:
            if os.path.exists(default_config_path):
                config_file = default_config_path
                try:
                    with open(config_file, 'r') as file:
                        config = json.load(file)
                    print(
                        f"Loaded default configuration from {default_config_path}."
                    )
                except json.JSONDecodeError:
                    print(
                        f"Default config file {default_config_path} is not valid JSON."
                    )
                except Exception as e:
                    print(
                        f"Error loading default config file {default_config_path}: {e}"
                    )

        # If default config is also invalid or not present, use built-in defaults
        if not config or not self.validate_config(config):
            print("Using built-in default configuration.")
            config = DEFAULT_CONFIG_CONTENT.copy()
            self.save_config(config)
            return config

        # Fix individual corrupted fields
        fixed_config = self.fix_corrupted_fields(config)
        self.save_config(fixed_config)
        return fixed_config

    def fix_corrupted_fields(self, config):
        """
        Fixes corrupted fields in a configuration by replacing them with defaults.

        Args:
            config (dict): The configuration to validate and fix.

        Returns:
            dict: A valid configuration with corrupted fields replaced by defaults.
        """
        fixed_config = DEFAULT_CONFIG_CONTENT.copy()
        any_fixes = False

        for key, default_value in DEFAULT_CONFIG_CONTENT.items():
            if key in config:
                value = config[key]
                if self.validate_config_field(key, value):
                    fixed_config[key] = value
                else:
                    fixed_config[key] = default_value
                    print(f"Replaced invalid value for '{key}' with default.")
                    any_fixes = True
            else:
                fixed_config[key] = default_value
                print(f"Missing key '{key}'. Added default value.")
                any_fixes = True

        # Optionally, handle additional properties if any (they should be ignored due to schema)
        return fixed_config

    def validate_config(self, config):
        """
        Validates the entire configuration against the JSON schema.

        Args:
            config (dict): The configuration to validate.

        Returns:
            bool: True if the configuration is fully valid, False otherwise.
        """
        try:
            validate(instance=config, schema=CONFIG_SCHEMA)
            return True
        except ValidationError as e:
            print(f"Configuration validation failed: {e.message}")
            return False

    def save_config(self, config):
        """Save the current configuration to the user config file."""
        base_directory = get_base_directory()
        config_directory = os.path.join(base_directory, 'assets', 'config')
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        try:
            with open(user_config_path, 'w') as file:
                json.dump(config, file, indent=4)
            print(f"Configuration saved to {self.user_config_file}.")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def reset_config_user(self):
        """Reset the user config file to the default configuration."""
        base_directory = get_base_directory()
        config_directory = os.path.join(base_directory, 'assets', 'config')
        default_config_path = os.path.join(config_directory,
                                           self.default_config_file)
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        try:
            if os.path.exists(default_config_path):
                with open(default_config_path, 'r') as default_file:
                    default_config = json.load(default_file)
                fixed_default_config = self.fix_corrupted_fields(
                    default_config)
                self.save_config(fixed_default_config)
                self.config = fixed_default_config
                print(
                    f"User configuration has been reset to defaults from {self.default_config_file}."
                )
            else:
                print(
                    f"Default config file {default_config_path} does not exist. Using built-in defaults."
                )
                self.config = DEFAULT_CONFIG_CONTENT.copy()
                self.save_config(self.config)
        except json.JSONDecodeError:
            print(
                f"Default config file {default_config_path} is not valid JSON."
            )
            print("Using built-in default configuration.")
            self.config = DEFAULT_CONFIG_CONTENT.copy()
            self.save_config(self.config)
        except Exception as e:
            print(f"Failed to reset user configuration: {e}")

    def get_config(self):
        """Get the current configuration."""
        return self.config

    def add_user_config(self):
        """Create a user config file if it doesn't exist."""
        base_directory = get_base_directory()
        config_directory = os.path.join(base_directory, 'assets', 'config')
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        # Check if the user config file exists
        if not os.path.exists(user_config_path):
            # Write the current config to the user config file
            try:
                with open(user_config_path, 'w') as file:
                    json.dump(self.config, file, indent=4)
                print(
                    f"Created {self.user_config_file} with the current configuration."
                )
            except Exception as e:
                print(f"Error while creating {self.user_config_file}: {e}")
        else:
            print(f"{self.user_config_file} already exists. No action taken.")

    def set_config_value(self, key, value, index=None):
        """Set a value in the configuration and save it to the user config file."""
        if key in ["fontColor", "dotColor"]:
            # Ensure value is a list of integers
            if isinstance(value, str):
                value = parse_rgba(value)
            elif isinstance(value, tuple):
                value = list(value)
            elif isinstance(value, list):
                # Validate list items
                if len(value) != 4 or not all(
                        isinstance(v, int) and 0 <= v <= 255 for v in value):
                    print(
                        f"Invalid value for '{key}'. Must be a list of four integers between 0 and 255."
                    )
                    return
        elif index is not None and isinstance(self.config.get(key), list):
            if not isinstance(value, type(DEFAULT_CONFIG_CONTENT[key][index])):
                print(
                    f"Invalid type for '{key}' at index {index}. Expected {type(DEFAULT_CONFIG_CONTENT[key][index])}."
                )
                return
        else:
            if not isinstance(value, type(DEFAULT_CONFIG_CONTENT[key])):
                print(
                    f"Invalid type for '{key}'. Expected {type(DEFAULT_CONFIG_CONTENT[key])}."
                )
                return

        if index is not None and isinstance(self.config.get(key), list):
            self.config[key][index] = value
        else:
            self.config[key] = value
        self.save_config(self.config)

    def __getitem__(self, key):
        return self.config.get(key)

    def __setitem__(self, key, value):
        self.set_config_value(key, value)
