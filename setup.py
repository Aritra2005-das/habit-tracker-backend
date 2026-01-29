"""
Setup script for initializing the database
"""
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('='*60)
    
    result = subprocess.run(command, cwd=Path(__file__).parent)
    if result.returncode != 0:
        print(f"Error: {description} failed")
        return False
    return True


def main():
    """Initialize the database"""
    print("Habit Tracker Backend Setup")
    print("="*60)
    
    # Create virtual environment
    print("\nSetup complete! To start:")
    print("1. Create and activate virtual environment:")
    print("   python -m venv venv")
    print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("\n2. Install dependencies:")
    print("   pip install -r requirements.txt")
    print("\n3. Run migrations:")
    print("   alembic upgrade head")
    print("\n4. Start the server:")
    print("   python -m uvicorn app.main:app --reload")
    print("\nAPI will be available at http://localhost:8000")
    print("Swagger docs at http://localhost:8000/docs")


if __name__ == "__main__":
    main()
