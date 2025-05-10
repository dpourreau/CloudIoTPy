#!/bin/bash

# CloudIoTPy Installation Script

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Display help information
show_help() {
    echo "CloudIoTPy Installation Script"
    echo ""
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev       Install with development dependencies"
    echo "  --help      Display this help message"
    echo ""
}

# Parse command line arguments
DEV_MODE=false

for arg in "$@"; do
    case $arg in
        --dev)
            DEV_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            show_help
            exit 1
            ;;
    esac
done

echo "Starting CloudIoTPy installation..."

# Create and activate virtual environment
echo "Creating virtual environment..."
python -m venv "$SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"

# Build sensor_py drivers
echo "Building sensor_py drivers..."
cd "$SCRIPT_DIR/sensor_py/drivers_c"
make clean && make
cd "$SCRIPT_DIR/sensor_py"

# Install sensor_py
echo "Installing sensor_py..."
pip install -e .

# Install CloudIoTPy
echo "Installing CloudIoTPy..."
cd "$SCRIPT_DIR"
if [ "$DEV_MODE" = true ]; then
    echo "Installing with development dependencies..."
    pip install -e ".[dev]"
else
    pip install -e .
fi

echo ""
echo "Installation complete!"
echo "To activate the virtual environment in the future, run:"
echo "source venv/bin/activate"
echo ""
