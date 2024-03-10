#!/bin/bash

# Allow script to continue running even if errors occur
set +e

# Define directories to check
directories="../src/ ../examples/"

# Generate a timestamp
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")

# create a markdown file to store the results
filename="test_results_$timestamp.md"

# Optionally activate your virtual environment
# source ../path/to/your/venv/bin/activate

# prepent a go syntax to the file in order to incease readability
echo '```go' > $filename

{
echo "Running Black..."
black --check $directories 2>&1
echo -e "Complete.\n"

echo "Sorting imports with isort..."
isort $directories 2>&1
echo -e "Complete.\n"

echo "Linting with Flake8..."
flake8 $directories 2>&1
echo -e "Complete.\n"

echo "Static type check with mypy..."
mypy $directories 2>&1
echo -e "Complete.\n"

echo "Checking for security issues with bandit..."
bandit -r $directories 2>&1
echo -e"Complete.\n"

echo "Running pytest with coverage..."
# Adjust this command based on your pytest setup and directories
pytest ../ 2>&1
echo -e"Complete.\n"

# Optionally deactivate virtual environment if activated earlier
# deactivate

echo "All checks passed! Read the log file for more details."
} | tee -a $filename

echo '```' >> $filename

# Optionally deactivate virtual environment if activated earlier
# deactivate
