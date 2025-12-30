#!/usr/bin/env python3
"""
Setup Verification Script for Quiz System
Run this to check if all dependencies are properly installed
"""

import sys
import importlib

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  ⚠️  Warning: Python 3.10+ recommended")
        return False
    return True


def check_module(module_name, display_name=None):
    """Check if a Python module is installed"""
    if display_name is None:
        display_name = module_name

    try:
        importlib.import_module(module_name)
        print(f"✓ {display_name}")
        return True
    except ImportError:
        print(f"✗ {display_name} - NOT INSTALLED")
        return False


def check_redis_connection():
    """Check if Redis server is accessible"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✓ Redis server (connected)")
        return True
    except Exception as e:
        print(f"✗ Redis server - NOT RUNNING ({str(e)})")
        return False


def check_file_structure():
    """Check if essential files exist"""
    import os

    essential_files = [
        'main.py',
        'config.py',
        'database.py',
        'models.py',
        'auth.py',
        '.env',
        'requirements.txt'
    ]

    all_exist = True
    for file in essential_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING")
            all_exist = False

    return all_exist


def main():
    print("=" * 50)
    print("Quiz System - Setup Verification")
    print("=" * 50)
    print()

    print("1. Checking Python Version...")
    python_ok = check_python_version()
    print()

    print("2. Checking Required Python Packages...")
    packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('redis', 'Redis'),
        ('pydantic', 'Pydantic'),
        ('jose', 'Python-JOSE'),
        ('passlib', 'Passlib'),
        ('jinja2', 'Jinja2'),
        ('pptx', 'python-pptx'),
        ('PIL', 'Pillow')
    ]

    packages_ok = all(check_module(mod, name) for mod, name in packages)
    print()

    print("3. Checking Redis Connection...")
    redis_ok = check_redis_connection()
    print()

    print("4. Checking File Structure...")
    files_ok = check_file_structure()
    print()

    print("=" * 50)
    print("Verification Summary")
    print("=" * 50)

    if python_ok and packages_ok and redis_ok and files_ok:
        print("✓ All checks passed! You're ready to start the server.")
        print()
        print("To start the server, run:")
        print("  python main.py")
        print()
        print("Or use the startup script:")
        print("  Windows: start_server.bat")
        print("  Linux/Mac: ./start_server.sh")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        if not packages_ok:
            print("To install missing packages, run:")
            print("  pip install -r requirements.txt")
        if not redis_ok:
            print("To start Redis server:")
            print("  redis-server")
        return 1


if __name__ == '__main__':
    sys.exit(main())
