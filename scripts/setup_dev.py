#!/usr/bin/env python3
"""
Development environment setup script for AGC.

This script helps new team members set up their development environment.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple


def run_command(command: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {description} completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False, e.stderr
    except FileNotFoundError:
        print(f"❌ Command not found: {' '.join(command)}")
        return False, "Command not found"


def check_python_version():
    """Check if Python version is compatible."""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version < (3, 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_system_dependencies():
    """Check for system-level dependencies."""
    print("🔍 Checking system dependencies...")
    
    system = platform.system().lower()
    missing_deps = []
    
    # Check for audio dependencies
    if system == "linux":
        # Check for ALSA/PulseAudio
        success, _ = run_command(["which", "aplay"], "Checking audio system")
        if not success:
            missing_deps.append("ALSA audio system (install alsa-utils)")
    
    elif system == "darwin":  # macOS
        # Check for Homebrew (recommended for dependencies)
        success, _ = run_command(["which", "brew"], "Checking Homebrew")
        if not success:
            print("⚠️  Homebrew not found. Consider installing for easier dependency management.")
    
    if missing_deps:
        print("❌ Missing system dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        return False
    
    print("✅ System dependencies check passed")
    return True


def setup_virtual_environment():
    """Set up Python virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    success, _ = run_command(
        [sys.executable, "-m", "venv", "venv"],
        "Creating virtual environment"
    )
    return success


def activate_virtual_environment():
    """Provide instructions for activating virtual environment."""
    system = platform.system().lower()
    
    if system == "windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"
    
    print(f"📝 To activate virtual environment, run: {activate_cmd}")


def install_dependencies():
    """Install Python dependencies."""
    # Determine pip path
    system = platform.system().lower()
    if system == "windows":
        pip_path = "venv\\Scripts\\pip"
    else:
        pip_path = "venv/bin/pip"
    
    # Upgrade pip first
    success, _ = run_command(
        [pip_path, "install", "--upgrade", "pip"],
        "Upgrading pip"
    )
    if not success:
        return False
    
    # Install requirements
    success, _ = run_command(
        [pip_path, "install", "-r", "requirements.txt"],
        "Installing Python dependencies"
    )
    if not success:
        return False
    
    # Install development dependencies
    success, _ = run_command(
        [pip_path, "install", "-e", ".[dev]"],
        "Installing development dependencies"
    )
    return success


def setup_environment_file():
    """Set up environment configuration file."""
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return False
    
    try:
        # Copy example to .env
        env_content = env_example.read_text()
        env_file.write_text(env_content)
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your API keys and settings")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def setup_pre_commit_hooks():
    """Set up pre-commit hooks for code quality."""
    system = platform.system().lower()
    if system == "windows":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    # Install pre-commit
    success, _ = run_command(
        [python_path, "-m", "pip", "install", "pre-commit"],
        "Installing pre-commit"
    )
    if not success:
        return False
    
    # Set up pre-commit hooks
    success, _ = run_command(
        [python_path, "-m", "pre_commit", "install"],
        "Setting up pre-commit hooks"
    )
    return success


def create_directories():
    """Create necessary directories."""
    directories = [
        "logs",
        "data/models",
        "data/audio/samples",
        "data/screenshots",
        "tests/fixtures",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")
    return True


def run_tests():
    """Run tests to verify setup."""
    system = platform.system().lower()
    if system == "windows":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    success, _ = run_command(
        [python_path, "-m", "pytest", "tests/", "-v", "--tb=short"],
        "Running test suite"
    )
    return success


def main():
    """Main setup function."""
    print("🚀 Setting up AGC development environment...")
    print("=" * 50)
    
    # Change to project directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working in: {project_root.absolute()}")
    
    setup_steps = [
        ("Python version", check_python_version),
        ("System dependencies", check_system_dependencies),
        ("Virtual environment", setup_virtual_environment),
        ("Python dependencies", install_dependencies),
        ("Environment file", setup_environment_file),
        ("Directories", create_directories),
        ("Pre-commit hooks", setup_pre_commit_hooks),
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        print(f"\n📋 Step: {step_name}")
        if not step_function():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n📝 Please resolve the errors above and run setup again.")
        return 1
    else:
        print("✅ Development environment setup completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Activate virtual environment:")
        activate_virtual_environment()
        print("   2. Edit .env file with your API keys")
        print("   3. Run: python src/main.py")
        print("\n🎉 Happy coding!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
