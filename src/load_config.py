import json
import os
import utils


class LoadConfig:

    def __init__(self,
                 default_config_file='config_default.json',
                 user_config_file='config_user.json'):
        self.default_config_file = default_config_file
        self.user_config_file = user_config_file
        self.config = self.load_config()

    def load_config(self):
        """
        Load configuration, prioritizing the user config file over the default config file.
        """
        base_directory = utils.get_base_directory()

        # Define paths for the config files
        config_directory = os.path.join(base_directory, 'assets', 'config')
        default_config_path = os.path.join(config_directory,
                                           self.default_config_file)
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        # Check for the user config file; fallback to the default config file
        config_file = user_config_path if os.path.exists(
            user_config_path) else default_config_path
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            print(f"Error: The file {config_file} was not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error: The file {config_file} is not a valid JSON.")
            return {}

    def get_config(self):
        return self.config

    def add_user_config(self):
        # Print the absolute path of the current directory
        base_directory = utils.get_base_directory()
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
        if index is not None and isinstance(self.config.get(key), list):
            self.config[key][index] = value
        else:
            self.config[key] = value
        self.save_config()

    def save_config(self):
        """Save the current configuration to the user config file."""
        # Print the absolute path of the current directory
        base_directory = utils.get_base_directory()
        config_directory = os.path.join(base_directory, 'assets', 'config')
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        try:
            with open(user_config_path, 'w') as file:
                json.dump(self.config, file, indent=4)
            print(f"Configuration saved to {self.user_config_file}.")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def reset_config_user(self):
        """Reset the user config file to the default configuration."""
        # Print the absolute path of the current directory
        current_directory = os.path.abspath(os.path.dirname(__file__))

        # Move up one directory to the parent directory
        parent_directory = os.path.abspath(
            os.path.join(current_directory, os.pardir))

        # Construct the absolute paths for the config files
        config_directory = os.path.join(parent_directory, 'config')
        default_config_path = os.path.join(config_directory,
                                           self.default_config_file)
        user_config_path = os.path.join(config_directory,
                                        self.user_config_file)

        try:
            with open(default_config_path, 'r') as default_file:
                default_config = json.load(default_file)

            with open(user_config_path, 'w') as user_file:
                json.dump(default_config, user_file, indent=4)

            # Update the current in-memory configuration
            self.config = default_config

            print(
                f"User configuration has been reset to default values from {self.default_config_file}."
            )
        except Exception as e:
            print(f"Failed to reset user configuration: {e}")

    def __getitem__(self, key):
        return self.config.get(key)

    def __setitem__(self, key, value):
        self.config[key] = value
