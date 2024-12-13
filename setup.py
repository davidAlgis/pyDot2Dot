"""
Setup script for building the 'dot 2 dot' application using cx_Freeze.
This script includes support for metadata generation and UPX compression.
"""

import os
import subprocess
from cx_Freeze import setup, Executable
from cx_Freeze.command.build_exe import build_exe
from metadata import generate_metadata, read_metadata


class BuildExeWithUPX(build_exe):
    """
    Custom build_exe class that compresses the resulting executables using UPX after the build.
    """

    def run(self):
        """
        Runs the standard build process and then compresses the .exe files with UPX.
        """
        # Run the standard build process
        super().run()

        # Get the output directory
        dist_dir = self.build_exe

        # Find and compress .exe files in the output directory
        for root, _, files in os.walk(dist_dir):
            for file in files:
                if file.endswith(".exe"):
                    exe_path = os.path.join(root, file)

                    # Skip unsupported files
                    if "arm64" in file.lower():
                        print(f"Skipping unsupported file: {exe_path}")
                        continue

                    print(f"Compressing {exe_path} with UPX...")
                    try:
                        subprocess.run(["upx", "--best", "--lzma", exe_path],
                                       check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"UPX compression failed for {exe_path}: {e}")


# Determine the base setting for Windows
BASE = "Win32GUI" if os.name == "nt" else None

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "dot2dot", "main.py")
ASSETS_PATH = os.path.join(SCRIPT_DIR, "assets")

# Specify application packages and files
PACKAGES = ["dot2dot", "dot2dot.gui", "numpy"]
INCLUDES = []
EXCLUDES = []
INCLUDE_FILES = [(ASSETS_PATH, "assets")]

# Create the executable
EXECUTABLES = [
    Executable(script=MAIN_SCRIPT,
               base=BASE,
               icon=os.path.join(ASSETS_PATH, "dot_2_dot.ico"),
               target_name="dot_2_dot.exe")
]

# Generate metadata and read it
generate_metadata()
metadata = read_metadata()

# Setup configuration
setup(
    name=metadata["name"],
    version=metadata["version"],
    author=metadata["author"],
    description="Visual tools to create \"dot to dot\" images.",
    options={
        "build_exe": {
            "packages": PACKAGES,
            "includes": INCLUDES,
            "excludes": EXCLUDES,
            "include_files": INCLUDE_FILES,
            "build_exe": os.path.join(SCRIPT_DIR, "build")
        }
    },
    executables=EXECUTABLES,
    cmdclass={"build_exe": BuildExeWithUPX},
)
