# Minimum CMake version
cmake_minimum_required(VERSION 3.10)

# Project name
project(dot_2_dot)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Define the source file and resource file
set(SOURCE_FILE app_launcher.cpp)
set(RESOURCE_FILE app_launcher.rc)

# Add the executable with the resource file for the icon
add_executable(dot_2_dot ${SOURCE_FILE} ${RESOURCE_FILE})
