#!/usr/bin/env python3
# --- KADDU YT-VIEWS SYSTEM: PRIORITIZED SETUP & BOOTSTRAP ---
# This section ensures all environment and dependency checks are performed BEFORE any imports that require them.
# This prevents ImportError and provides a robust, user-friendly startup sequence.

# --- MINIMAL STANDARD LIBRARY IMPORTS (ALWAYS AVAILABLE) ---
import os
import sys
import subprocess
import shutil
import importlib.util
import time
import threading
import platform

# --- SETUP FUNCTIONS (venv, dependency, binary checks) ---
# (All setup functions are already defined below in the script)

# --- PRIORITIZED SETUP EXECUTION ---
if __name__ == "__main__":
    # 1. Check for Python virtual environment
    def is_venv():
        return (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            os.environ.get('VIRTUAL_ENV') is not None
        )
    def require_venv_or_exit():
        print("\033[95m⚙️  Initializing KADDU YT-VIEWS System Setup...\033[0m")
        print("\033[94m🐍 Checking for Python virtual environment (venv)...\033[0m")
        if not is_venv():
            print("\033[91m❌ \033[1mCRITICAL: Not running in a Python virtual environment!\033[0m")
            print("\033[93m   This script \033[1mMUST\033[0m\033[93m be run inside a venv to avoid system-wide package conflicts and ensure correct dependency versions.\033[0m")
            print("\033[96mℹ️  \033[1mFollow these steps to create and activate a venv (Linux/macOS):\033[0m")
            print("\033[90m     1. Navigate to the script's directory in your terminal.\033[0m")
            print("\033[90m     2. Create venv: \033[1mpython3 -m venv .kaddu_venv\033[0m")
            print("\033[90m     3. Activate venv: \033[1msource .kaddu_venv/bin/activate\033[0m")
            print("\033[90m        (Your terminal prompt should now show '(.kaddu_venv)' prefix)\033[0m")
            print("\033[90m     4. Install dependencies inside venv: \033[1mpip install -r requirements.txt\033[0m")
            print("\033[90m     5. Run the script: \033[1mpython3 main.py\033[0m")
            print("\033[91m👉 Please set up and activate the virtual environment, then re-run the script. Exiting now.\033[0m")
            sys.exit(1)
        print("\033[92m✅ Python virtual environment detected and active.\033[0m")
        if os.name == 'posix' and hasattr(os, 'geteuid') and os.geteuid() == 0:
            print("\033[93m⚠️  WARNING: You are running as root. This is not recommended for Python venvs!\033[0m")
            print("\033[96mℹ️  If you need to use sudo, try: \033[1msudo -E python3 main.py\033[0m")
            print("\033[90m  (The -E flag preserves your venv environment variables for sudo)\033[0m")
    require_venv_or_exit()

    # 2. Check and install Python dependencies
    def check_and_install_python_dependencies():
        print("\033[94m📦 Checking Python dependencies (selenium, requests, PySocks, pyfiglet, rich)...\033[0m")
        required_modules = {
            "selenium": "selenium",
            "requests": "requests",
            "socks": "PySocks",
            "pyfiglet": "pyfiglet",
            "rich": "rich"
        }
        missing_packages = []
        for module_name, package_name in required_modules.items():
            try:
                importlib.import_module(module_name)
            except ImportError:
                missing_packages.append(package_name)
        if missing_packages:
            missing_packages_str = ", ".join(sorted(list(set(missing_packages))))
            print(f"\n\033[93m⚠️  Missing Python packages: \033[1m{missing_packages_str}\033[0m")
            req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
            if not os.path.exists(req_file):
                print("\033[91m❌ \033[1mCRITICAL: 'requirements.txt' not found!\033[0m")
                print("\033[93m   Cannot automatically install dependencies. Please create 'requirements.txt' with the following content or install manually:\033[0m")
                print("\033[90m--- requirements.txt ---\033[0m")
                for pkg in ["selenium", "requests[socks]", "PySocks", "pyfiglet", "rich"]:
                    print(f"\033[90m{pkg}\033[0m")
                print("\033[90m------------------------\033[0m")
                print(f"\n\033[93mℹ️  Manual Installation Guide:\033[0m")
                print("\033[96m  1. Create a requirements.txt file with the above content.\033[0m")
                print("\033[96m  2. Run: \033[1mpip install -r requirements.txt\033[0m")
                print("\033[96m  3. Then re-run: \033[1mpython3 main.py\033[0m")
                sys.exit(1)
            print(f"\033[96m👉 Installing dependencies from '{req_file}'...\033[0m")
            proc = subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", req_file], capture_output=True, text=True, timeout=240)
            if proc.returncode == 0:
                print(f"\n\033[92m✅🎉 All Python dependencies from requirements.txt installed successfully!\033[0m\n")
            else:
                print(f"\n\033[91m❌😢 Failed to install Python dependencies!\033[0m")
                print(f"\033[90mPip stdout:\n{proc.stdout}\033[0m")
                print(f"\033[90mPip stderr:\n{proc.stderr}\033[0m")
                sys.exit(1)
        else:
            print(f"\n\033[92m✅🎉 All required Python dependencies are already installed!\033[0m\n")
    check_and_install_python_dependencies()

    # 3. Check and install system dependencies (geckodriver, tor)
    def is_command_available(command):
        return shutil.which(command) is not None
    # (Insert ensure_geckodriver_available and ensure_tor_installed functions here, unchanged)
    # ... existing code ...
    ensure_geckodriver_available()
    ensure_tor_installed()

    # 4. Now that setup is complete, import modules that depend on setup
    # --- DELAYED IMPORTS: Only import after setup is confirmed ---
    # These imports require dependencies and binaries to be present.
    import re
    import random
    import concurrent.futures
    import itertools
    import urllib.request
    import zipfile
    import tarfile
    from urllib.parse import urlparse
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.webdriver.common.proxy import Proxy, ProxyType
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException, WebDriverException
    # Import pytor after setup
    try:
        import pytor
    except ImportError:
        print("\033[93m⚠️  pytor.py module not found. IP changing and advanced Tor management will be limited.\033[0m")
        pytor = None
    except Exception as e:
        print(f"\033[91m❌ Error importing pytor: {e}. IP changing may be affected.\033[0m")
        pytor = None

    # 5. Proceed to main logic
    # ... existing code ...
    # (Call main() as before)
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n\033[93m⚠️  Keyboard interrupt! Signaling stop...\033[0m")
        stop_event_global.set()
        print(f"\033[94mPlease wait for graceful shutdown...\033[0m")
        time.sleep(5)
    except SystemExit as e:
        if e.code != 0:
            print(f"\033[91m😢 Script exited (Code: {e.code}).\033[0m")
    except Exception as e_critical:
        print(f"\n\033[91m❌\033[1m --- CRITICAL UNEXPECTED ERROR --- \033[0m")
        print(f"\033[91mType: {type(e_critical).__name__}, Details: {e_critical}\033[0m")
        import traceback
        print(f"\033[90m--- Traceback --- \n{traceback.format_exc()}--- End Traceback ---\033[0m")
        print(f"\033[96mReport this issue on GitHub with the traceback.\033[0m")
    finally:
        print("\033[0m")
        print(f"\033[94mℹ️  KADDU YT-VIEWS program finished.\033[0m")
else:
    # If not __main__, do nothing (for import safety)
    pass
# --- END OF PRIORITIZED BOOTSTRAP ---
# --- MAIN LOGIC AND FUNCTION DEFINITIONS CONTINUE BELOW ---
# ... existing code ...
