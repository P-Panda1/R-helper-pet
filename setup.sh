#!/bin/bash
# Setup script for History Helper

echo "Setting up History Helper..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p models
mkdir -p cache/crawled_content
mkdir -p logs

# Check if Qdrant is running
echo "Checking Qdrant..."
if ! docker ps | grep -q qdrant; then
    echo "Qdrant is not running. Starting Qdrant container..."
    docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
    echo "Qdrant started on port 6333"
else
    echo "Qdrant is already running"
fi

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Ensure Qdrant is running: docker ps | grep qdrant"
echo "  3. Run: python main.py"

