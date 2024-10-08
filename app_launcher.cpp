#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>

// Function to execute a command and return its output
std::string exec(const char *cmd) {
  std::array<char, 128> buffer;
  std::string result;
  std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
  if (!pipe) {
    throw std::runtime_error("popen() failed!");
  }
  while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
    result += buffer.data();
  }
  return result;
}

int main(int argc, char *argv[]) {
  // Step 1: Check if Python is installed
  try {
    std::string python_version = exec("python --version");
    std::cout << "Python is installed: " << python_version;
  } catch (const std::runtime_error &e) {
    std::cerr << "Error: Python is not installed or not in PATH.\n";
    return 1;
  }

  // Step 2: Install requirements using pip
  std::cout << "Installing requirements...\n";
  int pip_result = system("pip install -r requirements.txt");
  if (pip_result != 0) {
    std::cerr << "Error: Failed to install requirements.\n";
    return 1;
  }

  // Step 3: Launch Python script with arguments
  std::string python_command = "python .\\main.py";
  for (int i = 1; i < argc; ++i) {
    python_command += " ";
    python_command += argv[i];
  }

  std::cout << "Launching Python script...\n";
  int python_result = system(python_command.c_str());
  if (python_result != 0) {
    std::cerr << "Error: Python script execution failed.\n";
    return 1;
  }

  return 0;
}