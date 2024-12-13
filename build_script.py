"""
This script automates the creation of a virtual environment, installation of dependencies,
and building of an executable. It is designed to be run as a standalone utility.
"""

import os
import subprocess
import sys
import venv


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
    and executable build process.
    """
    env_dir = os.path.join(
        os.getcwd(), "build_env")  # Directory for the virtual environment

    try:
        # Step 1: Create a virtual environment
        create_virtual_env(env_dir)

        # Step 2: Install requirements
        install_requirements(env_dir)

        # Step 3: Build the executable
        build_executable(env_dir)

        print("\nBuild process completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\nAn error occurred during the build process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
