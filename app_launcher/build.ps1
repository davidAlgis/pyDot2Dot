# Set script to stop on any error
$ErrorActionPreference = "Stop"

# Define paths
Write-Host $PSScriptRoot
$currentDir = Get-Location
$buildDir = Join-Path $PSScriptRoot "build"
$buildDirExe = Join-Path $buildDir "Release" # Updated to Release folder
$buildDirExe = Join-Path $buildDir "Release" # Updated to Release folder
$parentDir = Join-Path $PSScriptRoot ".."
$parentDir = [System.IO.Path]::GetFullPath($parentDir)
Write-Host $parentDir
$exeName = "dot_2_dot.exe"
$icoFile = "dot_2_dot.ico"

# Ensure the build directory exists
if (-Not (Test-Path $buildDir)) {
    New-Item -Path $buildDir -ItemType Directory
}

# Go into the build directory
Set-Location $buildDir

# Run CMake to configure the project with Release mode
cmake -DCMAKE_BUILD_TYPE=Release ..

# Run CMake to build the project in Release mode
cmake --build . --config Release

# Check if the executable was built
$exePath = Join-Path $buildDirExe $exeName
if (-Not (Test-Path $exePath)) {
    Write-Host "Error: Executable not found!"
    exit 1
}

# Copy the executable to the parent directory
$destinationPath = Join-Path $parentDir $exeName
Copy-Item $exePath -Destination $destinationPath -Force

# Confirm completion
Write-Host "Build completed successfully. Executable copied to $destinationPath"

# Go back to the original directory
Set-Location $currentDir
