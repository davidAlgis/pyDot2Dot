#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <string>

#ifdef _WIN32
#define popen _popen
#define pclose _pclose
#include <windows.h> // For GetModuleFileNameA
#else
#include <unistd.h> // For readlink on Unix-based systems
#endif

namespace fs = std::filesystem;

// Utility function to trim whitespace from a string (in place)
void trim(std::string &s) {
  s.erase(s.begin(), std::find_if(s.begin(), s.end(), [](unsigned char ch) {
            return !std::isspace(ch);
          }));
  s.erase(std::find_if(s.rbegin(), s.rend(),
                       [](unsigned char ch) { return !std::isspace(ch); })
              .base(),
          s.end());
}

// Function to get the path to the executable's directory
std::string get_executable_directory() {
  char buffer[1024];
#ifdef _WIN32
  GetModuleFileNameA(nullptr, buffer, sizeof(buffer));
#else
  ssize_t len = readlink("/proc/self/exe", buffer, sizeof(buffer) - 1);
  if (len != -1) {
    buffer[len] = '\0';
  }
#endif
  std::string exec_path(buffer);
  return fs::path(exec_path).parent_path().string();
}

// Function to create the temporary folder near the executable
fs::path get_temp_folder_path() {
  fs::path temp_folder = fs::path(get_executable_directory()) / "temp";
  if (!fs::exists(temp_folder)) {
    fs::create_directory(temp_folder);
    std::cout << "Created temp folder at: " << temp_folder << std::endl;
  }
  return temp_folder;
}

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

// Function to get the current git commit hash
std::string get_git_commit_hash() {
  try {
    std::string commit_hash = exec("git rev-parse HEAD");
    trim(commit_hash); // Trim any trailing whitespace/newlines
    std::cout << "Current git commit hash: " << commit_hash
              << std::endl; // Debug
    return commit_hash;
  } catch (...) {
    std::cerr << "Error: Failed to get git commit hash." << std::endl; // Debug
    return "";
  }
}

// Check if this is the first time the application is running
bool is_first_time_installed(const fs::path &temp_folder) {
  fs::path install_marker_file = temp_folder / ".installed";
  bool first_time = !fs::exists(install_marker_file);
  std::cout << "Is first time installed? " << (first_time ? "Yes" : "No")
            << std::endl; // Debug
  return first_time;
}

// Check if the git repository has been updated
bool git_has_updated(const fs::path &temp_folder) {
  std::string current_commit_hash = get_git_commit_hash();

  if (current_commit_hash.empty()) {
    std::cout << "No git repository found or failed to get commit hash."
              << std::endl; // Debug
    return false;           // No git repository, skip check
  }

  fs::path commit_hash_file = temp_folder / ".git_last_commit";
  if (!fs::exists(commit_hash_file)) {
    std::cout
        << "No last commit hash found. Assuming first-time install or update."
        << std::endl; // Debug
    return true;      // No commit hash recorded, consider as update
  }

  std::ifstream infile(commit_hash_file);
  std::string last_commit_hash;
  std::getline(infile, last_commit_hash);
  trim(last_commit_hash); // Trim any trailing whitespace/newlines

  std::cout << "last_commit_hash = " << last_commit_hash
            << " current_commit_hash = " << current_commit_hash
            << std::endl; // Debug

  bool has_updated = last_commit_hash != current_commit_hash;
  std::cout << "Has git updated? " << (has_updated ? "Yes" : "No")
            << std::endl; // Debug
  return has_updated;
}

// Update the last git commit hash
void update_git_commit_hash(const fs::path &temp_folder) {
  std::string current_commit_hash = get_git_commit_hash();
  fs::path commit_hash_file = temp_folder / ".git_last_commit";
  std::ofstream outfile(commit_hash_file);
  outfile << current_commit_hash;
  std::cout << "Updated git commit hash to: " << current_commit_hash
            << std::endl; // Debug
}

// Mark the application as installed
void mark_as_installed(const fs::path &temp_folder) {
  fs::path install_marker_file = temp_folder / ".installed";
  std::ofstream outfile(install_marker_file);
  outfile << "installed";
  std::cout << "Marked application as installed." << std::endl; // Debug
}

int main(int argc, char *argv[]) {
  try {
    // Step 1: Check if Python is installed
    std::string python_version = exec("python --version");
    std::cout << "Python is installed: " << python_version;
  } catch (const std::runtime_error &e) {
    std::cerr << "Error: Python is not installed or not in PATH.\n";
    return 1;
  }

  // Create a temp folder near the executable
  fs::path temp_folder = get_temp_folder_path();

  // Step 2: Install requirements if it's the first run or the git repo has been
  // updated
  fs::path requirements_file =
      fs::path(get_executable_directory()) / "src" / "requirements.txt";
  if (is_first_time_installed(temp_folder) || git_has_updated(temp_folder)) {
    std::cout << "Installing requirements...\n";
    std::string pip_command = "pip install -r " + requirements_file.string();
    int pip_result = system(pip_command.c_str());
    if (pip_result != 0) {
      std::cerr << "Error: Failed to install requirements.\n";
      return 1;
    }

    // Mark the application as installed and update the git commit hash
    mark_as_installed(temp_folder);
    update_git_commit_hash(temp_folder);
  } else {
    std::cout << "Requirements already installed. Skipping installation...\n";
  }

  // Step 3: Launch Python script with arguments
  fs::path python_script =
      fs::path(get_executable_directory()) / "src" / "main.py";
  std::string python_command = "python " + python_script.string();
  for (int i = 1; i < argc; ++i) {
    python_command += " ";
    python_command += argv[i];
  }

  std::cout << "Launching Python script: " << python_command
            << std::endl; // Debug
  int python_result = system(python_command.c_str());
  if (python_result != 0) {
    std::cerr << "Error: Python script execution failed.\n";
    return 1;
  }

  std::cout << "Python script executed successfully." << std::endl; // Debug
  return 0;
}
