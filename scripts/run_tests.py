#!/usr/bin/env python3
"""
Test runner script for AGC project.

This script provides various testing options for the development team.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


def run_command(command: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {' '.join(command)}")
        return False


def get_python_path() -> str:
    """Get the path to Python executable in virtual environment."""
    import platform
    system = platform.system().lower()
    if system == "windows":
        return "venv\\Scripts\\python"
    else:
        return "venv/bin/python"


def run_unit_tests(component: Optional[str] = None, verbose: bool = False) -> bool:
    """Run unit tests."""
    python_path = get_python_path()
    
    if component:
        test_path = f"tests/unit/{component}/"
        description = f"Running unit tests for {component}"
    else:
        test_path = "tests/unit/"
        description = "Running all unit tests"
    
    command = [python_path, "-m", "pytest", test_path]
    
    if verbose:
        command.append("-v")
    
    command.extend(["--tb=short", "--strict-markers"])
    
    return run_command(command, description)


def run_integration_tests(verbose: bool = False) -> bool:
    """Run integration tests."""
    python_path = get_python_path()
    
    command = [python_path, "-m", "pytest", "tests/integration/"]
    
    if verbose:
        command.append("-v")
    
    command.extend(["--tb=short", "--strict-markers"])
    
    return run_command(command, "Running integration tests")


def run_coverage_tests() -> bool:
    """Run tests with coverage reporting."""
    python_path = get_python_path()
    
    command = [
        python_path, "-m", "pytest",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "tests/"
    ]
    
    success = run_command(command, "Running tests with coverage")
    
    if success:
        print("📊 Coverage report generated in htmlcov/index.html")
    
    return success


def run_linting() -> bool:
    """Run code linting."""
    python_path = get_python_path()
    
    # Run flake8
    flake8_success = run_command(
        [python_path, "-m", "flake8", "src/", "tests/"],
        "Running flake8 linting"
    )
    
    # Run mypy
    mypy_success = run_command(
        [python_path, "-m", "mypy", "src/"],
        "Running mypy type checking"
    )
    
    return flake8_success and mypy_success


def run_formatting_check() -> bool:
    """Check code formatting with black."""
    python_path = get_python_path()
    
    return run_command(
        [python_path, "-m", "black", "--check", "--diff", "src/", "tests/"],
        "Checking code formatting"
    )


def format_code() -> bool:
    """Format code with black."""
    python_path = get_python_path()
    
    return run_command(
        [python_path, "-m", "black", "src/", "tests/"],
        "Formatting code"
    )


def run_all_checks() -> bool:
    """Run all quality checks."""
    checks = [
        ("Linting", run_linting),
        ("Formatting check", run_formatting_check),
        ("Unit tests", lambda: run_unit_tests(verbose=True)),
        ("Integration tests", lambda: run_integration_tests(verbose=True)),
        ("Coverage tests", run_coverage_tests),
    ]
    
    failed_checks = []
    
    for check_name, check_function in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        if not check_function():
            failed_checks.append(check_name)
    
    print(f"\n{'='*50}")
    
    if failed_checks:
        print("❌ Some checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        return False
    else:
        print("✅ All checks passed!")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run tests and quality checks for AGC")
    
    parser.add_argument(
        "--component",
        choices=["voice_input", "screen_capture", "ai_agent", "voice_response", "game_integration"],
        help="Run tests for specific component only"
    )
    
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "coverage", "lint", "format", "format-check", "all"],
        default="unit",
        help="Type of tests/checks to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    
    print(f"🧪 Running {args.type} tests/checks...")
    print(f"📁 Working directory: {project_root.absolute()}")
    
    success = False
    
    if args.type == "unit":
        success = run_unit_tests(args.component, args.verbose)
    elif args.type == "integration":
        success = run_integration_tests(args.verbose)
    elif args.type == "coverage":
        success = run_coverage_tests()
    elif args.type == "lint":
        success = run_linting()
    elif args.type == "format":
        success = format_code()
    elif args.type == "format-check":
        success = run_formatting_check()
    elif args.type == "all":
        success = run_all_checks()
    
    if success:
        print("\n🎉 All tests/checks completed successfully!")
        return 0
    else:
        print("\n💥 Some tests/checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
