#!/bin/bash
# Backend setup script

set -e

echo "========================================"
echo "Habit Tracker Backend Setup"
echo "========================================"

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Edit .env with your database configuration"
fi

# Run migrations
echo ""
echo "Running database migrations..."
alembic upgrade head

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --reload"
echo ""
echo "API will be available at: http://localhost:8000"
echo "Swagger docs at: http://localhost:8000/docs"
