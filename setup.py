from cx_Freeze import setup, Executable
import sys
import os
import subprocess
from cx_Freeze.command.build_exe import build_exe


class build_exe_with_upx(build_exe):

    def run(self):
        # Run the standard build
        super().run()

        # After build is completed, run UPX on the resulting executables
        dist_dir = self.build_exe  # Output directory for the build

        # Find all .exe files in the dist_dir
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                if file.endswith(".exe"):
                    exe_path = os.path.join(root, file)

                    # Check for unsupported files and skip them
                    if "arm64" in file.lower():
                        print(f"Skipping unsupported file: {exe_path}")
                        continue

                    print(f"Compressing {exe_path} with UPX...")
                    try:
                        subprocess.run(["upx", "--best", "--lzma", exe_path],
                                       check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"UPX failed for {exe_path}: {e}")


# Base settings
base = None

# New architecture paths:
main_script = "D:\\Recherches\\pyDot2Dot\\dot2dot\\main.py"
assets_path = "D:\\Recherches\\pyDot2Dot\\assets"

# Specify the packages in your application
packages = ["dot2dot", "dot2dot.gui", "numpy"]
includes = []
excludes = []

# Include the entire assets folder
include_files = [(assets_path, "assets")]

executables = [
    Executable(script=main_script,
               base=base,
               icon="D:\\Recherches\\pyDot2Dot\\assets\\dot_2_dot.ico",
               target_name="dot_2_dot.exe")
]

setup(name="dot_2_dot",
      version="1.0",
      description="Your Application Description",
      options={
          "build_exe": {
              "packages": packages,
              "includes": includes,
              "excludes": excludes,
              "include_files": include_files,
              "build_exe": "D:\\Recherches\\pyDot2Dot\\build"
          }
      },
      executables=executables,
      cmdclass={"build_exe": build_exe_with_upx})
