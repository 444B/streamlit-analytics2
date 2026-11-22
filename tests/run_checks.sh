#!/usr/bin/env bash

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NO_COLOR='\033[0m'

# Strict mode - but we'll handle errors ourselves
set -uo pipefail

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/../src/streamlit_analytics2"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/../pyproject.toml"
LOG_DIR="${SCRIPT_DIR}/logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
RESULTS_FILE="${LOG_DIR}/test_results_${TIMESTAMP}.md"
ERROR_LOG="${LOG_DIR}/errors_${TIMESTAMP}.log"
PARALLEL_JOBS=6
GLOBAL_ERROR=0

# Initialize log directory
mkdir -p "${LOG_DIR}"

# Improved error handler function
error_handler() {
    local exit_code=$1
    local line_no=$2
    local last_command=$3
    
    # Only log actual errors (ignore expected failures from tests/checks)
    if [[ $exit_code -ne 0 && "$last_command" != *"run_check"* ]]; then
        echo -e "\n${RED}Script error occurred:${NO_COLOR}"
        echo -e "${RED}Line: ${line_no}${NO_COLOR}"
        echo -e "${RED}Command: ${last_command}${NO_COLOR}"
        echo -e "${RED}Exit code: ${exit_code}${NO_COLOR}"
        
        # Log the error
        {
            echo "Timestamp: $(date)"
            echo "Script error occurred:"
            echo "Line: ${line_no}"
            echo "Command: ${last_command}"
            echo "Exit code: ${exit_code}"
            echo "----------------"
        } >> "${ERROR_LOG}"
        
        GLOBAL_ERROR=1
    fi
}

trap 'error_handler $? ${LINENO} "$BASH_COMMAND"' ERR

# Help function with improved documentation
show_help() {
    cat << EOF
Usage: ./run_checks.sh [OPTIONS]

A comprehensive code quality check script that runs various formatters,
linters, and tests on your Python codebase.

Options:
    -h, --help              Show this help message
    -f, --fix              Run formatters and linters in fix mode
    -p, --parallel         Run checks in parallel (default: serial)
    -v, --verbose          Show detailed output
    -s, --skip-venv        Skip virtual environment check/creation
    --no-format           Skip format checks
    --no-lint             Skip lint checks
    --no-type             Skip type checks
    --no-test             Skip tests
    --no-security         Skip security checks
    --ci                  Run in CI mode (implies --skip-venv)

Examples:
    ./run_checks.sh                    # Run all checks in check-only mode
    ./run_checks.sh --fix              # Run and fix formatting issues
    ./run_checks.sh --parallel         # Run checks in parallel
    ./run_checks.sh --no-format --fix  # Run all checks except formatting in fix mode

Environment Variables:
    PYTHON_VERSION        Python version to use (default: 3.11)
    COVERAGE_THRESHOLD    Minimum required coverage percentage (default: 80)
    CI                   Set to 'true' when running in CI environment

EOF
    exit 0
}

# Parse command line arguments
FIX_MODE=false
PARALLEL_MODE=false
VERBOSE=false
SKIP_VENV=false
RUN_FORMAT=true
RUN_LINT=true
RUN_TYPE=true
RUN_TEST=true
RUN_SECURITY=true
CI_MODE=false

while (( "$#" )); do
    case "$1" in
        -h|--help)
            show_help
            ;;
        -f|--fix)
            FIX_MODE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -s|--skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --no-format)
            RUN_FORMAT=false
            shift
            ;;
        --no-lint)
            RUN_LINT=false
            shift
            ;;
        --no-type)
            RUN_TYPE=false
            shift
            ;;
        --no-test)
            RUN_TEST=false
            shift
            ;;
        --no-security)
            RUN_SECURITY=false
            shift
            ;;
        --ci)
            CI_MODE=true
            SKIP_VENV=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NO_COLOR}"
            show_help
            ;;
    esac
done

# Function to print formatted section headers
print_section() {
    local title="$1"
    local char="${2:-=}"
    local width=50
    local padding=$(( (width - ${#title} - 2) / 2 ))
    local line=$(printf "%${width}s" | tr " " "$char")
    echo -e "\n${BLUE}${line}${NO_COLOR}"
    echo -e "${BLUE}${char}${char}${NO_COLOR} ${CYAN}${title}${NO_COLOR} ${BLUE}${char}${char}${NO_COLOR}"
    echo -e "${BLUE}${line}${NO_COLOR}\n"
}

# Function to check command existence
check_command() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${RED}Error: ${cmd} is not installed${NO_COLOR}"
        echo "Please install it first. You can try:"
        case "$cmd" in
            uv)
                echo "pip install uv"
                ;;
            black|isort|flake8|mypy|bandit|pytest)
                echo "pip install $cmd"
                ;;
            *)
                echo "Unable to provide installation instructions for $cmd"
                ;;
        esac
        exit 1
    fi
}

# Improved run_check function with better error handling
run_check() {
    local name="$1"
    local cmd="$2"
    local start_time=$(date +%s)
    local check_failed=0
    
    print_section "Running ${name}"
    
    if [ "$VERBOSE" = true ]; then
        echo "Command: $cmd"
    fi
    
    # Create a temporary file for command output
    local temp_output=$(mktemp)
    
    # Run the command and capture output
    if eval "$cmd" > "$temp_output" 2>&1; then
        local status="passed"
        local color="$GREEN"
    else
        local status="failed"
        local color="$RED"
        check_failed=1
        GLOBAL_ERROR=1
    fi
    
    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Display result
    echo -e "${color}${name} ${status} (${duration}s)${NO_COLOR}"
    
    # If verbose or failed, show output
    if [ "$VERBOSE" = true ] || [ "$status" = "failed" ]; then
        cat "$temp_output"
    fi
    
    # Log output
    {
        echo "=== ${name} ==="
        echo "Status: ${status}"
        echo "Duration: ${duration}s"
        echo "Command: ${cmd}"
        echo "Output:"
        cat "$temp_output"
        echo -e "================\n"
    } >> "$ERROR_LOG"
    
    rm "$temp_output"
    
    # Return success/failure without using $(...)
    if [ $check_failed -eq 1 ]; then
        return 1
    else
        return 0
    fi
}

# Function to setup virtual environment
setup_venv() {
    print_section "Setting up virtual environment"
    
    # Check if venv exists and requirements are up to date
    if [ -f "${VENV_DIR}/pyvenv.cfg" ]; then
        local venv_creation_time=$(stat -c %Y "${VENV_DIR}/pyvenv.cfg" 2>/dev/null || stat -f %m "${VENV_DIR}/pyvenv.cfg")
        local requirements_mod_time=$(stat -c %Y "${REQUIREMENTS_FILE}" 2>/dev/null || stat -f %m "${REQUIREMENTS_FILE}")
        
        if [ "$venv_creation_time" -gt "$requirements_mod_time" ]; then
            echo -e "${GREEN}Virtual environment is up to date${NO_COLOR}"
            return 0
        fi
    fi
    
    echo "Creating/updating virtual environment..."
    check_command uv
    
    # Remove existing venv if it exists
    rm -rf "${VENV_DIR}"
    
    # Create new venv and install dependencies
    uv venv "${VENV_DIR}"
    source "${VENV_DIR}/bin/activate"
    uv pip install -e "..[dev]"
}

# Function to run parallel checks with proper error handling
run_parallel_checks() {
    local -a pids=()
    local -A commands=(
        ["Black formatting"]="black ${SRC_DIR} $([ "$FIX_MODE" = true ] && echo '--quiet' || echo '--check --verbose')"
        ["Import sorting"]="isort ${SRC_DIR} $([ "$FIX_MODE" = true ] && echo '--quiet' || echo '--check-only --verbose --diff')"
        ["Flake8 linting"]="flake8 ${SRC_DIR}"
        ["MyPy type checking"]="mypy ${SRC_DIR} --config-file ../mypy.ini"
        ["Bandit security check"]="bandit -r ${SRC_DIR}"
    )
    
    for name in "${!commands[@]}"; do
        (run_check "$name" "${commands[$name]}") &
        pids+=($!)
    done
    
    # Wait for all background processes
    for pid in "${pids[@]}"; do
        wait $pid || true  # Don't exit if a check fails
    done
}

# Initialize results file with markdown formatting
{
    echo "# Code Quality Check Results"
    echo "Run on: $(date)"
    echo "Mode: $([ "$FIX_MODE" = true ] && echo 'Fix' || echo 'Check')"
    echo "Environment: $([ "$CI_MODE" = true ] && echo 'CI' || echo 'Local')"
    echo ""
    echo '```text'
} > "$RESULTS_FILE"

# Setup virtual environment if needed
if [ "$SKIP_VENV" = false ] && [ -z "${VIRTUAL_ENV:-}" ]; then
    setup_venv
fi

# Run checks
if [ "$PARALLEL_MODE" = true ]; then
    run_parallel_checks
else
    # Format checks
    if [ "$RUN_FORMAT" = true ]; then
        if [ "$FIX_MODE" = true ]; then
            run_check "Black formatting" "black ${SRC_DIR} --quiet" || true
            run_check "Import sorting" "isort ${SRC_DIR} --quiet" || true
        else
            run_check "Black formatting" "black ${SRC_DIR} --check --verbose" || true
            run_check "Import sorting" "isort ${SRC_DIR} --check-only --verbose --diff" || true
        fi
    fi
    
    # Lint checks
    if [ "$RUN_LINT" = true ]; then
        run_check "Flake8 linting" "flake8 ${SRC_DIR}" || true
    fi
    
    # Type checks
    if [ "$RUN_TYPE" = true ]; then
        run_check "MyPy type checking" "mypy ${SRC_DIR} --config-file ../mypy.ini" || true
    fi
    
    # Security checks
    if [ "$RUN_SECURITY" = true ]; then
        run_check "Bandit security check" "bandit -r ${SRC_DIR}" || true
    fi
    
    # Tests with coverage
    if [ "$RUN_TEST" = true ]; then
        if [ "$CI_MODE" = true ]; then
            run_check "Pytest with coverage" "pytest ../ --cov=${SRC_DIR} --cov-report=xml --cov-report=term-missing:skip-covered" || true
        else
            run_check "Pytest with coverage" "pytest ../ --cov=${SRC_DIR} --cov-report=term-missing:skip-covered" || true
        fi
    fi
fi

# Print summary
print_section "Summary"
if [ $GLOBAL_ERROR -eq 0 ]; then
    echo -e "${GREEN}✨ All checks passed! Ready for production.${NO_COLOR}"
else
    echo -e "${RED}❌ Some checks failed. Please review the log for details.${NO_COLOR}"
    if [ "$FIX_MODE" = false ]; then
        echo -e "${YELLOW}💡 Tip: Try running with --fix to automatically fix formatting issues${NO_COLOR}"
    fi
fi

# Finalize markdown file
echo '```' >> "$RESULTS_FILE"

# Add error log if there are any errors
if [ -s "$ERROR_LOG" ]; then
    {
        echo -e "\n## Detailed Error Log"
        echo '```text'
        cat "$ERROR_LOG"
        echo '```'
    } >> "$RESULTS_FILE"
fi

# Optional: Open the results file
if [ "$CI_MODE" = false ]; then
    if command -v code >/dev/null 2>&1; then
        code "$RESULTS_FILE" "$ERROR_LOG"
    elif command -v open >/dev/null 2>&1; then
        open "$RESULTS_FILE"
    fi
fi

exit $GLOBAL_ERROR