from cx_Freeze import setup, Executable
import sys
import os

# Base settings
base = None

# New architecture paths:
main_script = "D:\\Recherches\\pyDot2Dot\\dot2dot\\main.py"
assets_path = "D:\\Recherches\\pyDot2Dot\\assets"

# Specify the packages in your application
packages = [
    "dot2dot", "dot2dot.gui", "skimage", "skimage.morphology", "numba",
    "matplotlib", "numpy"
]
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
      executables=executables)
