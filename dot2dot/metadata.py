import json
import os
import subprocess
from dot2dot.utils import get_base_directory

base_directory = get_base_directory()

# Define paths for the config files
config_directory = os.path.join(base_directory, 'assets', 'config')
# Path to the metadata file
METADATA_FILE = os.path.join(config_directory, 'metadata.json')


def get_git_commit_id():
    """
    Retrieves the current Git commit ID of the repository.
    
    Returns:
        str: The current commit ID or "Unknown" if Git is not initialized or an error occurs.
    """
    try:
        # Run `git rev-parse HEAD` to get the current commit hash
        commit_id = subprocess.check_output(['git', 'rev-parse',
                                             'HEAD']).strip().decode('utf-8')
        return commit_id
    except subprocess.CalledProcessError:
        return "Unknown"


def read_metadata():
    """
    Reads and retrieves the metadata from the metadata.json file.
    
    Returns:
        dict: Parsed JSON content from metadata.json file.
    """
    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(f"{METADATA_FILE} not found.")

    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    return metadata


def generate_metadata():
    """
    Generates and writes the metadata.json file in the config folder.
    Retrieves the current Git commit ID automatically.
    """
    commit_id = get_git_commit_id()
    software_version = "0.1"

    metadata = {
        "name": "dot 2 dot",
        "author": "David Algis",
        "version": software_version,
        "commit": commit_id
    }

    # Ensure the config folder exists
    config_folder = os.path.dirname(METADATA_FILE)
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)

    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata has been written to {METADATA_FILE}")


if __name__ == "__main__":
    generate_metadata()
