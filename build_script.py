import os
import subprocess
import sys
import venv


def create_virtual_env(env_dir):
    """
    Creates a virtual environment in the specified directory.
    """
    print(f"Creating virtual environment in {env_dir}...")
    venv.EnvBuilder(clear=True, with_pip=True).create(env_dir)


def install_requirements(env_dir):
    """
    Installs the required modules into the virtual environment.
    """
    pip_path = os.path.join(env_dir, "Scripts",
                            "pip") if os.name == "nt" else os.path.join(
                                env_dir, "bin", "pip")
    print("Installing requirements...")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)


def build_executable(env_dir):
    """
    Builds the executable using the virtual environment's Python interpreter.
    """
    python_path = os.path.join(env_dir, "Scripts",
                               "python") if os.name == "nt" else os.path.join(
                                   env_dir, "bin", "python")
    print("Building the executable...")
    subprocess.run([python_path, "setup.py", "build_exe"], check=True)


if __name__ == "__main__":
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
