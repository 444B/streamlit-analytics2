#!/bin/bash

# Allow script to continue running even if errors occur
set +e

# Define directories to check
directories="../src/ ../examples/"

# Generate a timestamp
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
filename="test_results_$timestamp.txt"

# Optionally activate your virtual environment
# source ../path/to/your/venv/bin/activate

{
echo "Running Black..."
black --check $directories 2>&1

echo "Sorting imports with isort..."
isort $directories --check-only 2>&1

echo "Linting with Flake8..."
flake8 $directories 2>&1

echo "Static type check with mypy..."
mypy $directories 2>&1

echo "Checking for security issues with bandit..."
bandit -r $directories 2>&1

echo "Running pytest with coverage..."
# Adjust this command based on your pytest setup and directories
pytest ../ 2>&1

# Optionally deactivate virtual environment if activated earlier
# deactivate

echo "All checks passed!"
} | tee $filename
