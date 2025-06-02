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

# --- EARLY DEFINITIONS: Setup functions and globals used in prioritized setup ---
# These must be defined before their first use in the setup sequence.

# Global stop event for thread control (used in main and elsewhere)
stop_event_global = threading.Event()

# --- SETUP FUNCTIONS (venv, dependency, binary checks) ---
# (All setup functions are already defined below in the script)

# --- ensure_geckodriver_available definition (moved up from below) ---
def ensure_geckodriver_available():
    import stat
    GECKO_URL_BASE = "https://github.com/mozilla/geckodriver/releases/latest/download/"
    drivers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drivers")
    os.makedirs(drivers_dir, exist_ok=True)
    geckodriver_name = "geckodriver.exe" if os.name == "nt" else "geckodriver"
    gecko_local_path = os.path.join(drivers_dir, geckodriver_name)
    if shutil.which("geckodriver"):
        print(f"\033[92m✅ geckodriver is already available in PATH.\033[0m")
        return
    if os.path.exists(gecko_local_path):
        if os.name != "nt" and not os.access(gecko_local_path, os.X_OK):
            try:
                os.chmod(gecko_local_path, os.stat(gecko_local_path).st_mode | stat.S_IEXEC)
                print(f"\033[92mℹ️  Made geckodriver in ./drivers/ executable.\033[0m")
            except Exception as e:
                print(f"\033[93m⚠️  Could not set executable permission on geckodriver: {e}\033[0m")
        os.environ["PATH"] = drivers_dir + os.pathsep + os.environ["PATH"]
        print(f"\033[92m✅ geckodriver found in ./drivers/. Added to PATH for this session.\033[0m")
        if shutil.which("geckodriver"):
            print(f"\033[92m✅ geckodriver confirmed in PATH after adding ./drivers/.\033[0m")
        else:
            print(f"\033[93m⚠️  Added ./drivers/ to PATH, but geckodriver still not found by shutil.which(). Manual check needed.\033[0m")
        return
    sys_plat = platform.system().lower()
    arch = platform.machine().lower()
    if sys_plat.startswith("win"):
        gecko_asset = "geckodriver-latest-win64.zip" if "64" in arch else "geckodriver-latest-win32.zip"
    elif sys_plat == "darwin":
        gecko_asset = "geckodriver-latest-macos-aarch64.tar.gz" if arch == "arm64" else "geckodriver-latest-macos.tar.gz"
    elif sys_plat == "linux":
        if arch in ("x86_64", "amd64"):
            gecko_asset = "geckodriver-latest-linux64.tar.gz"
        elif arch in ("aarch64", "arm64"):
            gecko_asset = "geckodriver-latest-linux-aarch64.tar.gz"
        elif arch == "armv7l":
            gecko_asset = "geckodriver-latest-linux-arm7hf.tar.gz"
        else:
            print(f"\033[91m❌ Unsupported Linux architecture for geckodriver: {arch}\033[0m")
            print(f"\033[96mℹ️  Please download geckodriver manually for your system and place it in the PATH or in the ./drivers/ directory.\033[0m")
            print(f"\033[96mℹ️  Download geckodriver manually from: https://github.com/mozilla/geckodriver/releases/latest\033[0m")
            try:
                import webbrowser
                webbrowser.open("https://github.com/mozilla/geckodriver/releases/latest")
            except Exception:
                pass
            return
    else:
        print(f"\033[91m❌ Unsupported OS for geckodriver: {sys_plat}\033[0m")
        print(f"\033[96mℹ️  Please download geckodriver manually for your system and place it in the PATH or in the ./drivers/ directory.\033[0m")
        print(f"\033[96mℹ️  Download geckodriver manually from: https://github.com/mozilla/geckodriver/releases/latest\033[0m")
        try:
            import webbrowser
            webbrowser.open("https://github.com/mozilla/geckodriver/releases/latest")
        except Exception:
            pass
        return
    gecko_url = GECKO_URL_BASE + gecko_asset
    print(f"\033[96mℹ️  Downloading geckodriver from: {gecko_url}\033[0m")
    archive_path = os.path.join(drivers_dir, gecko_asset)
    try:
        import urllib.request
        urllib.request.urlretrieve(gecko_url, archive_path)
    except Exception as e:
        print(f"\033[91m❌ Failed to download geckodriver: {e}\033[0m")
        print(f"\033[96mℹ️  Please download geckodriver manually and place it in the PATH or in the ./drivers/ directory.\033[0m")
        return
    try:
        import zipfile, tarfile
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(drivers_dir)
        elif archive_path.endswith(".tar.gz"):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                for member in tar_ref.getmembers():
                    if member.name == geckodriver_name or member.name.endswith('/' + geckodriver_name):
                        member.name = os.path.basename(member.name)
                        tar_ref.extract(member, drivers_dir)
                        break
                else:
                    tar_ref.extractall(drivers_dir)
        else:
            print(f"\033[91m❌ Unknown archive format for geckodriver: {archive_path}\033[0m")
            return
        print(f"\033[92m✅ geckodriver extracted to {drivers_dir}\033[0m")
    except Exception as e:
        print(f"\033[91m❌ Failed to extract geckodriver: {e}\033[0m")
        return
    finally:
        try:
            if os.path.exists(archive_path): os.remove(archive_path)
        except Exception:
            pass
    if not os.path.exists(gecko_local_path):
        print(f"\033[91m❌ geckodriver not found at {gecko_local_path} after extraction. Please check the archive contents or install manually.\033[0m")
        print(f"\033[96mℹ️  Download geckodriver manually from: https://github.com/mozilla/geckodriver/releases/latest\033[0m")
        try:
            import webbrowser
            webbrowser.open("https://github.com/mozilla/geckodriver/releases/latest")
        except Exception:
            pass
        return
    if os.name != "nt":
        try:
            os.chmod(gecko_local_path, os.stat(gecko_local_path).st_mode | stat.S_IEXEC)
        except Exception as e:
            print(f"\033[93m⚠️  Could not set executable permission on geckodriver at {gecko_local_path}: {e}\033[0m")
    os.environ["PATH"] = drivers_dir + os.pathsep + os.environ["PATH"]
    if shutil.which("geckodriver"):
        print(f"\033[92m✅ geckodriver is ready and added to PATH for this session!\033[0m")
    else:
        print(f"\033[93m⚠️  geckodriver downloaded and extracted to ./drivers/, and ./drivers/ added to PATH, but shutil.which() still cannot find it. Selenium might fail if geckodriver is not discoverable. Ensure {gecko_local_path} is executable and correctly named.\033[0m")

# --- ensure_tor_installed definition (moved up from below) ---
def ensure_tor_installed():
    print(f"\n\033[94m🧅 Checking Tor installation ('tor' command availability)...\033[0m")
    def is_command_available(command):
        return shutil.which(command) is not None
    if not is_command_available("tor"):
        print(f"\033[93m⚠️  'tor' command not found. Attempting to install Tor (may require sudo privileges)...\033[0m")
        installer = None
        install_cmd_update = None
        install_cmd_tor = None
        if is_command_available("apt-get"):
            installer = "apt-get"
            install_cmd_update = ["sudo", "apt-get", "update", "-y", "-qq"]
            install_cmd_tor = ["sudo", "apt-get", "install", "tor", "-y", "-qq"]
        elif is_command_available("yum"):
            installer = "yum"
            install_cmd_tor = ["sudo", "yum", "install", "-y", "-q", "tor"]
        elif is_command_available("dnf"):
            installer = "dnf"
            install_cmd_tor = ["sudo", "dnf", "install", "-y", "--quiet", "tor"]
        elif is_command_available("pacman"):
            installer = "pacman"
            install_cmd_tor = ["sudo", "pacman", "-S", "--noconfirm", "--quiet", "tor"]
        if installer:
            print(f"\033[96m👉 Using '{installer}' to install Tor...\033[0m")
            success = False
            error_output = ""
            try:
                if install_cmd_update:
                    proc_update = subprocess.run(install_cmd_update, capture_output=True, stderr=subprocess.PIPE, text=True, timeout=300)
                    if proc_update.returncode != 0:
                        error_output += f"Update failed with {installer}: {proc_update.stderr}\n"
                    else:
                        proc_tor = subprocess.run(install_cmd_tor, capture_output=True, stderr=subprocess.PIPE, text=True, timeout=300)
                        if proc_tor.returncode == 0:
                            success = True
                        else:
                            error_output += f"Tor install failed with {installer}: {proc_tor.stderr}\n"
                else:
                    proc_tor = subprocess.run(install_cmd_tor, capture_output=True, stderr=subprocess.PIPE, text=True, timeout=300)
                    if proc_tor.returncode == 0:
                        success = True
                    else:
                        error_output += f"Tor install failed with {installer}: {proc_tor.stderr}\n"
            except subprocess.TimeoutExpired:
                error_output = f"Tor installation with {installer} timed out after 5 minutes."
                success = False
            except Exception as e:
                error_output = f"Exception during Tor installation with {installer}: {str(e)}"
                success = False
            if success and is_command_available("tor"):
                print(f"\n\033[92m✅🎉 Tor command installed successfully using {installer}!\033[0m\n")
            else:
                print(f"\n\033[91m❌😢 Failed to install 'tor' command using {installer}.\033[0m")
                if error_output.strip():
                    print(f"\033[90mError details:\n{error_output.strip()}\033[0m")
                print(f"\033[93mℹ️  Please try installing Tor manually for your system (e.g., 'sudo {installer} install tor') and ensure the 'tor' command is in your PATH, then re-run this script.\033[0m")
                print(f"\033[96mℹ️  Download Tor from: https://www.torproject.org/download/\033[0m")
                try:
                    import webbrowser
                    webbrowser.open("https://www.torproject.org/download/")
                except Exception:
                    pass
                sys.exit(1)
        else:
            print(f"\n\033[91m❌😢 Could not detect a supported package manager (apt-get, yum, dnf, pacman) to install Tor.\033[0m")
            print(f"\033[93mℹ️  Please install Tor manually for your system so that the 'tor' command is available in your PATH, then re-run the script.\033[0m")
            print(f"\033[96mℹ️  Download Tor from: https://www.torproject.org/download/\033[0m")
            try:
                import webbrowser
                webbrowser.open("https://www.torproject.org/download/")
            except Exception:
                pass
            sys.exit(1)
    else:
        print(f"\n\033[92m✅🎉 'tor' command is already available!\033[0m\n")

# --- main function definition (move from below) ---
def main():
    # ... main logic as already defined ...
    pass

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
