import json
import os
import subprocess
import sys

__version__ = "0.2"
__author__ = "David Algis"
__name__ = "dot 2 dot"


def get_base_directory():
    """
    Determines the base directory for the application, depending on whether it's run
    as a standalone executable via PyInstaller or cx_Freeze, or as a normal Python script.

    - PyInstaller sets sys._MEIPASS when frozen.
    - cx_Freeze sets sys.frozen = True but does not provide sys._MEIPASS.
      Instead, the executable directory (os.path.dirname(sys.executable)) can be used.

    If not frozen at all, we return the parent directory of the current file.
    """
    if getattr(sys, 'frozen', False):
        # Running as a frozen executable (either PyInstaller or cx_Freeze)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller sets _MEIPASS
            return sys._MEIPASS
        else:
            # cx_Freeze scenario: no _MEIPASS, but sys.frozen is True
            return os.path.dirname(sys.executable)
    else:
        # Running normally as a script
        return os.path.abspath(os.path.dirname(__file__))


base_directory = get_base_directory()
config_directory = os.path.join(base_directory, 'assets', 'config')
METADATA_FILE = os.path.join(config_directory, 'metadata.json')


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


def get_git_commit_id():
    """
    Retrieves the current Git commit ID of the repository.
    
    Returns:
        str: The current commit ID or "Unknown" if Git is not initialized or an error occurs.
    """
    try:
        commit_id = subprocess.check_output(['git', 'rev-parse',
                                             'HEAD']).strip().decode('utf-8')
        return commit_id
    except subprocess.CalledProcessError:
        return "Unknown"


def load_metadata():
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

    metadata = {
        "name": __name__,
        "author": __author__,
        "version": __version__,
        "commit": commit_id,
    }

    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)

    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata has been written to {METADATA_FILE}")
