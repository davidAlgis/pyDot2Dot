"""
This script automates the creation of a virtual environment, installation of dependencies,
and building of an executable. It is designed to be run as a standalone utility.
"""

import os
import subprocess
import sys
import venv
import shutil


def create_virtual_env(env_dir_path):
    """
    Creates a virtual environment in the specified directory.

    Args:
        env_dir_path (str): Path to the directory where the virtual environment will be created.
    """
    print(f"Creating virtual environment in {env_dir_path}...")
    venv.EnvBuilder(clear=True, with_pip=True).create(env_dir_path)


def install_requirements(env_dir_path):
    """
    Installs the required modules into the virtual environment.

    Args:
        env_dir_path (str): Path to the virtual environment directory.
    """
    pip_path = os.path.join(env_dir_path, "Scripts",
                            "pip") if os.name == "nt" else os.path.join(
                                env_dir_path, "bin", "pip")
    print("Installing requirements...")
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"],
                       check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        raise


def build_executable(env_dir_path):
    """
    Builds the executable using the virtual environment's Python interpreter.

    Args:
        env_dir_path (str): Path to the virtual environment directory.
    """
    python_path = os.path.join(env_dir_path, "Scripts",
                               "python") if os.name == "nt" else os.path.join(
                                   env_dir_path, "bin", "python")
    print("Building the executable...")
    try:
        subprocess.run([python_path, "setup.py", "build_exe"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to build the executable: {e}")
        raise


def main():
    """
    Main function to orchestrate the virtual environment creation, dependency installation,
    and executable build process. Additionally, excludes the 'assets/config' folder from
    the build if 'config_user.json' exists within it by moving only the 'config_user.json' file.
    """
    env_dir = os.path.join(
        os.getcwd(), "build_env")  # Directory for the virtual environment
    assets_config_path = os.path.join(os.getcwd(), "assets", "config")
    config_user_file = os.path.join(assets_config_path, "config_user.json")
    backup_config_path = os.path.join(os.getcwd(), "config_backup")
    backup_config_file = os.path.join(
        backup_config_path, "config_user.json")  # Full path for backup

    backup_done = False  # Flag to indicate if backup was performed

    try:
        # Step 0: Check if 'config_user.json' exists
        if os.path.exists(config_user_file):
            print(
                f"Detected 'config_user.json' in {assets_config_path}. Excluding it from the build."
            )
            # Ensure the backup directory exists
            os.makedirs(backup_config_path, exist_ok=True)

            # Move 'config_user.json' to the backup directory
            shutil.move(config_user_file, backup_config_file)
            print(f"Moved 'config_user.json' to '{backup_config_file}'.")
            backup_done = True
        else:
            print(
                f"No 'config_user.json' found in {assets_config_path}. Including all assets in the build."
            )

        # Step 1: Create a virtual environment
        create_virtual_env(env_dir)

        # Step 2: Install requirements
        install_requirements(env_dir)

        # Step 3: Build the executable
        build_executable(env_dir)

        print("\nBuild process completed successfully.")
    except Exception as e:
        print(f"\nAn error occurred during the build process: {e}")
        sys.exit(1)
    finally:
        # Restore the 'config_user.json' file if it was backed up
        if backup_done:
            try:
                shutil.move(backup_config_file, assets_config_path)
                print(
                    f"Restored 'config_user.json' from '{backup_config_file}' to '{assets_config_path}'."
                )

                # Check if the backup directory is empty and remove it if so
                if os.path.exists(backup_config_path
                                  ) and not os.listdir(backup_config_path):
                    shutil.rmtree(backup_config_path)
                    print(
                        f"Removed empty backup directory '{backup_config_path}'."
                    )
                elif os.path.exists(backup_config_path) and os.listdir(
                        backup_config_path):
                    print(
                        f"Backup directory '{backup_config_path}' is not empty. Not removing."
                    )
            except Exception as e:
                print(f"Failed to restore 'config_user.json' from backup: {e}")
                print(
                    "Please check the state of your 'assets' and 'config_backup' directories."
                )
                sys.exit(1)


if __name__ == "__main__":
    main()
