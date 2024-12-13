"""
Module for managing application metadata and retrieving Git commit information.
"""

import json
import os
import subprocess
import sys

# Application Metadata
__version__ = "0.2"
__author__ = "David Algis"
APP_NAME = "dot 2 dot"


def get_base_directory():
    """
    Determines the base directory for the application, depending on whether it's run
    as a standalone executable or as a normal Python script.

    - cx_Freeze sets sys.frozen = True but does not provide sys._MEIPASS.
      Instead, the executable directory (os.path.dirname(sys.executable)) can be used.

    Returns:
        str: Base directory for the application.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # cx_Freeze case
    return os.path.abspath(os.path.dirname(__file__))  # Running as a script


BASE_DIRECTORY = get_base_directory()
CONFIG_DIRECTORY = os.path.join(BASE_DIRECTORY, 'assets', 'config')
METADATA_FILE = os.path.join(CONFIG_DIRECTORY, 'metadata.json')


def read_metadata():
    """
    Reads and retrieves the metadata from the metadata.json file.

    Returns:
        dict: Parsed JSON content from metadata.json file.
    
    Raises:
        FileNotFoundError: If the metadata file does not exist.
    """
    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(f"{METADATA_FILE} not found.")

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_git_commit_id():
    """
    Retrieves the current Git commit ID of the repository.

    Returns:
        str: The current commit ID or "Unknown" if Git is not initialized or an error occurs.
    """
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                       text=True).strip()
    except subprocess.CalledProcessError:
        return "Unknown"


def generate_metadata():
    """
    Generates and writes the metadata.json file in the config folder.
    Retrieves the current Git commit ID automatically.
    """
    metadata = {
        "name": APP_NAME,
        "author": __author__,
        "version": __version__,
        "commit": get_git_commit_id(),
    }

    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata has been written to {METADATA_FILE}")
