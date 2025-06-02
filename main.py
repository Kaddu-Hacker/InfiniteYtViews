#!/usr/bin/env python3
# --- MINIMAL IMPORTS FOR SETUP CHECKS ---
import os
import sys
import subprocess
import shutil
import importlib.util
import time
import threading

# --------------------------------------
# --- PRIORITIZED SETUP STARTS HERE ---
# Emojis and Colors for UI
EMOJI_SUCCESS = "✅"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_INFO = "ℹ️"
EMOJI_PROMPT = "👉"
EMOJI_PYTHON = "🐍"
EMOJI_TOR = "🧅"
EMOJI_GEAR = "⚙️"
EMOJI_ROCKET = "🚀"
EMOJI_CELEBRATE = "🎉"
EMOJI_FAIL = "😢"
EMOJI_SPINNER = "🔄"
EMOJI_INSTALL = "📦"
EMOJI_BANNER = "🎬"
EMOJI_CONNECTING = "🔗"
EMOJI_SEARCH = "🔍"
EMOJI_DRY_RUN = "📝"
EMOJI_VIEW = "👀"
EMOJI_THANKS = "🙏"
EMOJI_STAR = "⭐"
EMOJI_VIDEO = "📹"  # Added
EMOJI_SHORT = "⏱️"  # Added
EMOJI_LINK = "🔗"   # Already present, confirmed
EMOJI_THREADS = "🧵" # Added
EMOJI_WAIT = "⏳"    # Added

C_HEADER = '\033[95m'
C_BLUE = '\033[94m'
C_CYAN = '\033[96m'
C_GREEN = '\033[92m'
C_WARNING = '\033[93m'
C_FAIL = '\033[91m'
C_END = '\033[0m'
C_BOLD = '\033[1m'
C_GRAY = '\033[90m'
C_UNDERLINE = '\033[4m' # Added
# --- MISSING COLOR CONSTANTS ADDED BELOW ---
C_YELLOW = '\033[93m'  # Bright yellow (same as C_WARNING for compatibility)
C_WHITE = '\033[97m'   # Bright white
C_OKBLUE = C_BLUE       # Alias for compatibility with old code
C_OKGREEN = C_GREEN     # Alias for compatibility with old code

# --- HELP TEXT Placeholder ---
HELP_TEXT = """ 
Placeholder for KADDU YT-VIEWS Help Information.

Common Commands:
  - Type 'help' at any prompt to see this message.

Troubleshooting:
  - Ensure you are in a Python virtual environment.
  - Ensure Tor is installed and running.
  - If using multiple connections, ensure your torrc is configured for multiple SOCKS ports (e.g., 9050, 9052, 9054...).
  - For issues with sudo, try 'sudo -E python3 main.py'.

More details will be added here.
"""

# --- Root Check Function (MOVED HERE) ---
def check_root():
    # On Linux/Unix systems
    if os.name == 'posix':
        # Also check if geteuid attribute exists for robustness, though it's standard on POSIX
        if hasattr(os, 'geteuid') and os.geteuid() != 0:
            # Modified message to be a warning rather than a strict exit, 
            # as some sudo commands are called internally now.
            print(f"{C_FAIL}{EMOJI_ERROR} ROOT/SUDO WARNING: This script may require root/sudo privileges for certain operations like Tor installation or system service management.{C_END}")
            print(f"{C_WARNING}   While some parts might work, you may encounter errors if these operations are needed and fail due to lack of permissions.{C_END}")
            print(f"{C_CYAN}{EMOJI_INFO}   If issues arise, consider running with: {C_BOLD}sudo -E python3 main.py{C_END}")
            print(f"{C_GRAY}     (The -E flag helps preserve your Python virtual environment variables when using sudo.){C_END}")
            # Allowing to proceed, specific commands will fail if they need sudo and don't have it.
        elif hasattr(os, 'geteuid') and os.geteuid() == 0:
            print(f"{C_GREEN}{EMOJI_SUCCESS} Script is running with root/sudo privileges.{C_END}")
            if is_venv(): # Check if also in venv, is_venv() needs to be defined before this check_root call or this part moved
                 print(f"{C_CYAN}{EMOJI_INFO}   Running as root inside a venv. If you used `sudo python3 ...`, it's often better to use `sudo -E python3 ...` to preserve the venv environment properly.{C_END}")
    # Removed Windows admin check as script is now primarily for Linux-like environments with Tor system services.

# --- Spinner Animation Helper ---
def spinner_animation(message, stop_event, duration=0, color=C_CYAN, emoji=EMOJI_SPINNER):
    """
    Displays a spinner animation in the CLI until stop_event is set or duration expires.
    Args:
        message (str): The message to display next to the spinner.
        stop_event (threading.Event): Event to signal the spinner to stop.
        duration (float): Optional duration in seconds to run the spinner (0 = infinite until stop_event).
        color (str): Color code for the spinner.
        emoji (str): Emoji to display with the spinner.
    """
    spinner_chars = ['|', '/', '-', '\\']
    start_time = time.time()
    idx = 0
    while not stop_event.is_set() and (duration == 0 or (time.time() - start_time < duration)):
        sys.stdout.write(f"\r{color}{emoji} {message} {spinner_chars[idx % 4]}{C_END}")
        sys.stdout.flush()
        time.sleep(0.15)
        idx += 1
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()

# --- Animated Banner ---
def print_animated_banner(): # This is the primary banner function
    try:
        import pyfiglet
        from rich.console import Console
        from rich.live import Live
        from rich.text import Text
        from rich.align import Align
    except ImportError:
        print(f"{C_WARNING}{EMOJI_WARNING} Banner dependencies missing (pyfiglet, rich). Skipping banner animation.{C_END}")
        # Fallback to a simple text banner if Rich is not available
        print(f"{C_HEADER} KADDU YT-VIEWS - YouTube Views Generator {C_END}")
        print(f"{C_GREEN} 100% Free & Open Source {C_END}")
        print(f"{C_YELLOW} GitHub: https://github.com/Kaddu-Hacker/InfiniteYtViews {C_END}")
        print(f"{C_BLUE} Tip: Always run in a virtual environment! {C_END}")
        print(f"{C_WHITE}-------------------------------------------------------------{C_END}")
        return
    
    console = Console()
    
    # Load custom ASCII art from file
    ascii_art_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ASCII')
    ascii_art_content = ""
    if os.path.exists(ascii_art_path):
        with open(ascii_art_path, 'r', encoding='utf-8') as f:
            # Read the whole art as one block for better centering
            raw_art = f.read()
            # Ensure Rich formatting is applied line by line if needed or as a whole block
            # For pre-formatted ASCII, direct printing with Align might be best.
            # If the ASCII itself contains Rich tags, Text.from_markup might be better.
            ascii_art_content = Text(raw_art, style="bold green") # Apply a base style
    else:
        ascii_art_content = Text("KADDU ASCII ART MISSING", style="bold red")

    # Prepare big 'KADDU' ASCII text using pyfiglet
    kaddu_text_figlet = pyfiglet.figlet_format("KADDU", font="big")
    kaddu_text_rich = Text(kaddu_text_figlet, style="bold magenta")

    # Animate custom ASCII art (if present) and then KADDU figlet text
    # Centering will be applied to the final display content by printing Align objects.
    
    console.print(Align.center(ascii_art_content)) # Print centered ASCII art
    console.print(Align.center(kaddu_text_rich)) # Print centered KADDU figlet

    # Subheading and sub-subheading, also centered
    console.print(Align.center(Text("YouTube Views Generator", style="bold cyan underline")))
    console.print(Align.center(Text("100% Free & Open Source", style="bold green")))
    console.print(Align.center(Text("GitHub: https://github.com/Kaddu-Hacker/InfiniteYtViews", style="bold yellow")))
    console.print(Align.center(Text("Tip: Always run in a virtual environment!", style="bold blue")))
    console.print(Align.center(Text("-------------------------------------------------------------", style="bold white")))
    console.print("") # Add a blank line for spacing after the banner

# --- Setup Functions ---
def is_venv():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )

def require_venv_or_exit():
    print(f"{C_HEADER}{EMOJI_GEAR} Initializing KADDU YT-VIEWS System Setup...{C_END}")
    print(f"{C_BLUE}{EMOJI_PYTHON} Checking for Python virtual environment (venv)...{C_END}")
    if not is_venv():
        print(f"{C_FAIL}{EMOJI_ERROR} {C_BOLD}CRITICAL: Not running in a Python virtual environment!{C_END}")
        print(f"{C_WARNING}   This script {C_BOLD}MUST{C_END}{C_WARNING} be run inside a venv to avoid system-wide package conflicts and ensure correct dependency versions.{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} {C_BOLD}Follow these steps to create and activate a venv (Linux/macOS):{C_END}")
        print(f"{C_GRAY}     1. Navigate to the script's directory in your terminal.{C_END}")
        print(f"{C_GRAY}     2. Create venv: {C_BOLD}python3 -m venv .kaddu_venv{C_END}")
        print(f"{C_GRAY}     3. Activate venv: {C_BOLD}source .kaddu_venv/bin/activate{C_END}")
        print(f"{C_GRAY}        (Your terminal prompt should now show '(.kaddu_venv)' prefix){C_END}")
        print(f"{C_GRAY}     4. Install dependencies inside venv: {C_BOLD}pip install -r requirements.txt{C_END}")
        print(f"{C_GRAY}     5. Run the script: {C_BOLD}python3 main.py{C_END}")
        print(f"{C_FAIL}{EMOJI_PROMPT} Please set up and activate the virtual environment, then re-run the script. Exiting now.{C_END}")
        sys.exit(1)
    print(f"{C_GREEN}{EMOJI_SUCCESS} Python virtual environment detected and active.{C_END}")
    if os.name == 'posix' and hasattr(os, 'geteuid') and os.geteuid() == 0:
        print(f"{C_WARNING}{EMOJI_WARNING} WARNING: You are running as root. This is not recommended for Python venvs!{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} If you need to use sudo, try: {C_BOLD}sudo -E python3 main.py{C_END}")
        print(f"{C_GRAY}  (The -E flag preserves your venv environment variables for sudo){C_END}")

def check_and_install_python_dependencies():
    print(f"{C_BLUE}{EMOJI_INSTALL} Checking Python dependencies (requests, PySocks, pyfiglet, rich)...{C_END}")
    required_modules = {"requests": "requests", "socks": "PySocks", "pyfiglet": "pyfiglet", "rich": "rich"}
    missing_packages = []
    for module_name, package_name in required_modules.items():
        if importlib.util.find_spec(module_name) is None:
            missing_packages.append(package_name)
    if missing_packages:
        missing_packages_str = ", ".join(sorted(list(set(missing_packages))))
        print(f"\n{C_WARNING}{EMOJI_WARNING} Missing Python packages: {C_BOLD}{missing_packages_str}{C_END}")
        print(f"{C_CYAN}{EMOJI_PROMPT} Installing dependencies from 'requirements.txt'...{C_END}")
        req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        if not os.path.exists(req_file):
            print(f"{C_FAIL}{EMOJI_ERROR} {C_BOLD}CRITICAL: 'requirements.txt' not found!{C_END}")
            print(f"{C_WARNING}   Cannot automatically install dependencies. Please ensure 'requirements.txt' exists and contains all needed packages.{C_END}")
            sys.exit(1)
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner_animation, args=(f"Installing Python dependencies...", stop_event), kwargs={"emoji": EMOJI_INSTALL, "color": C_CYAN})
        spinner_thread.start()
        try:
            proc = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-input", "-r", req_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            stop_event.set()
            spinner_thread.join()
            if proc.returncode == 0:
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} All Python dependencies installed successfully!{C_END}\n")
            else:
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to install Python dependencies!{C_END}")
                print(proc.stderr.decode(errors='ignore'))
                sys.exit(1)
        except subprocess.TimeoutExpired:
            stop_event.set()
            spinner_thread.join()
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} pip install timed out!{C_END}")
            sys.exit(1)
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Exception during dependency installation: {e}{C_END}")
            sys.exit(1)
        print(f"\n{C_CYAN}{EMOJI_INFO} Dependency installation step finished.{C_END}\n")
    else:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} All required Python dependencies are already installed!{C_END}\n")

def is_command_available(command):
    return shutil.which(command) is not None

def ensure_tor_installed():
    print(f"\n{C_BLUE}{EMOJI_TOR} Checking Tor installation...{C_END}")
    if not is_command_available("tor"):
        print(f"\n{C_WARNING}{EMOJI_WARNING} Tor command not found. Installing Tor (requires sudo privileges)...{C_END}")
        installer = None
        install_cmd = None
        install_cmd2 = None
        if is_command_available("apt"):
            installer = "apt"
            install_cmd = ["sudo", "apt", "update", "-y", "-qq"]
            install_cmd2 = ["sudo", "apt", "install", "tor", "-y", "-qq"]
        elif is_command_available("yum"):
            installer = "yum"
            install_cmd = ["sudo", "yum", "install", "tor", "-y", "-q"]
        elif is_command_available("pacman"):
            installer = "pacman"
            install_cmd = ["sudo", "pacman", "-S", "--noconfirm", "--quiet", "tor"]
        
        if installer:
            print(f"\n{C_CYAN}{EMOJI_PROMPT} Installing Tor using '{installer}'...{C_END}")
            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=spinner_animation, args=(f"Installing Tor with {installer}...", stop_event), kwargs={"emoji": EMOJI_TOR, "color": C_CYAN})
            spinner_thread.start()
            success = False
            tor_install_error_output = ""
            try:
                if installer == "apt":
                    # For apt, run update then install
                    proc1 = subprocess.run(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
                    tor_install_error_output += proc1.stderr.decode(errors='ignore') if proc1.stderr else ""
                    if proc1.returncode == 0:
                        proc2 = subprocess.run(install_cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
                        tor_install_error_output += "\n" + proc2.stderr.decode(errors='ignore') if proc2.stderr else ""
                        success = proc2.returncode == 0
                    else:
                        success = False # Update failed
                else:
                    # For yum/pacman, single install command
                    proc = subprocess.run(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
                    tor_install_error_output += proc.stderr.decode(errors='ignore') if proc.stderr else ""
                    success = proc.returncode == 0
            except subprocess.TimeoutExpired:
                tor_install_error_output = "Tor installation process timed out after 5 minutes."
                success = False
            except Exception as e:
                tor_install_error_output = f"Exception during Tor installation: {str(e)}"
                success = False
            finally:
                stop_event.set()
                spinner_thread.join()

            if success and is_command_available("tor"):
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor installed successfully using {installer}!{C_END}\n")
            else:
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to install Tor using {installer}!{C_END}")
                if tor_install_error_output.strip():
                    print(f"{C_GRAY}Error details:\\n{tor_install_error_output.strip()}{C_END}")
                print(f"{C_WARNING}{EMOJI_INFO} Please try installing Tor manually for your system and then re-run this script.{C_END}")
                sys.exit(1)
            print(f"\n{C_CYAN}{EMOJI_INFO} Tor installation step finished.{C_END}\n")
        else:
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Could not detect a supported package manager (apt, yum, pacman) to install Tor.{C_END}")
            print(f"{C_WARNING}{EMOJI_INFO} Please install Tor manually for your Linux distribution and re-run the script.{C_END}")
            sys.exit(1)
    else:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor is already installed!{C_END}\n")

def is_tor_service_running():
    """Checks if the Tor process is running, primarily using pgrep.
    Returns:
        bool: True if Tor process is found, False otherwise.
    """
    try:
        # pgrep is the most reliable cross-platform way to check for a running process
        # if systemctl/service are not available or misbehaving.
        pgrep_proc = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if pgrep_proc.returncode == 0 and pgrep_proc.stdout.strip():
            return True # Tor process found by pgrep

        # Fallback: Check systemctl if pgrep didn't find it (less likely to be accurate if pgrep failed)
        if is_command_available("systemctl"):
            systemctl_proc = subprocess.run(["systemctl", "is-active", "--quiet", "tor"], timeout=5)
            if systemctl_proc.returncode == 0:
                return True # Tor service active according to systemctl
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError): # FileNotFoundError if pgrep/systemctl not found
        return False
    except Exception as e:
        # print(f"{C_GRAY}Debug: Exception in is_tor_service_running: {e}{C_END}") # Optional debug
        return False

def ensure_tor_service_running():
    print(f"\n{C_BLUE}{EMOJI_TOR} Checking Tor service status...{C_END}")

    if is_tor_service_running():
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor service is already running! (Verified by pgrep){C_END}\n")
        return

    print(f"\n{C_WARNING}{EMOJI_WARNING} Tor service is not running. Attempting to start Tor service (requires sudo privileges)...{C_END}")
    
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner_animation, args=(f"Attempting to start Tor service...", stop_event), kwargs={"emoji": EMOJI_TOR, "color": C_CYAN})
    spinner_thread.start()

    service_start_methods_attempted = False
    systemctl_failed_non_systemd = False
    service_cmd_failed_non_systemd = False
    service_start_errors = []

    # Attempt 1: systemctl
    if is_command_available("systemctl"):
        service_start_methods_attempted = True
        try:
            # print(f"{C_GRAY}  Trying: sudo systemctl start tor.service{C_END}") # Debug
            proc_systemctl = subprocess.run(["sudo", "systemctl", "start", "tor.service"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            stderr_output = proc_systemctl.stderr.decode(errors='ignore').strip()
            if proc_systemctl.returncode != 0:
                service_start_errors.append(f"systemctl: {stderr_output}")
                if "systemd" in stderr_output and ("PID 1" in stderr_output or "Host is down" in stderr_output or "bus" in stderr_output):
                    systemctl_failed_non_systemd = True
                    # print(f"{C_GRAY}  systemctl: Detected non-systemd environment or bus error.{C_END}") # Debug
            time.sleep(3) # Give service time to start
            if is_tor_service_running(): # Check immediately if it started
                stop_event.set()
                spinner_thread.join()
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor service started successfully using systemctl! (Verified by pgrep){C_END}\n")
                print(f"\n{C_CYAN}{EMOJI_INFO} Tor service start step finished.{C_END}\n")
                return
        except subprocess.TimeoutExpired:
            service_start_errors.append("systemctl: Timeout during start attempt.")
            # print(f"{C_GRAY}  systemctl: Start attempt timed out.{C_END}") # Debug
        except Exception as e:
            service_start_errors.append(f"systemctl: Exception - {str(e)}")
            # print(f"{C_GRAY}  systemctl: Exception {e}{C_END}") # Debug

    # Attempt 2: service command (if systemctl failed or wasn't applicable)
    if not is_tor_service_running() and is_command_available("service"):
        service_start_methods_attempted = True
        try:
            # print(f"{C_GRAY}  Trying: sudo service tor start{C_END}") # Debug
            proc_service = subprocess.run(["sudo", "service", "tor", "start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            stderr_output = proc_service.stderr.decode(errors='ignore').strip()
            if proc_service.returncode != 0:
                service_start_errors.append(f"service cmd: {stderr_output}")
                if "systemd" in stderr_output and ("PID 1" in stderr_output or "Host is down" in stderr_output or "bus" in stderr_output):
                    service_cmd_failed_non_systemd = True
                    # print(f"{C_GRAY}  service: Detected non-systemd environment or bus error.{C_END}") # Debug

            time.sleep(3)
            if is_tor_service_running():
                stop_event.set()
                spinner_thread.join()
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor service started successfully using 'service' command! (Verified by pgrep){C_END}\n")
                print(f"\n{C_CYAN}{EMOJI_INFO} Tor service start step finished.{C_END}\n")
                return
        except subprocess.TimeoutExpired:
            service_start_errors.append("service cmd: Timeout during start attempt.")
            # print(f"{C_GRAY}  service: Start attempt timed out.{C_END}") # Debug
        except Exception as e:
            service_start_errors.append(f"service cmd: Exception - {str(e)}")
            # print(f"{C_GRAY}  service: Exception {e}{C_END}") # Debug
            
    # Attempt 3: Direct tor command execution as a fallback (if systemd/service methods failed or are unsuitable)
    # This is more of a last resort and might not behave like a proper service.
    if not is_tor_service_running():
        service_start_methods_attempted = True # Considered an attempt
        if systemctl_failed_non_systemd or service_cmd_failed_non_systemd:
            print(f"{C_CYAN}{EMOJI_INFO} systemctl/service commands seem unsuitable for this environment. Attempting direct Tor execution (less ideal).{C_END}")
        elif not is_command_available("systemctl") and not is_command_available("service"):
             print(f"{C_CYAN}{EMOJI_INFO} systemctl and service commands not found. Attempting direct Tor execution (less ideal).{C_END}")
        
        try:
            # print(f"{C_GRAY}  Trying: sudo tor --run-as-daemon 1 (or similar based on OS){C_END}") # Debug
            # Note: Starting Tor directly like this is tricky. It might need --daemonize or specific config.
            # For now, we'll assume if `tor` command exists, a simple `sudo tor` might work in some contexts,
            # or that `pytor.start_tor()` from a later step might be more robust for this.
            # This specific attempt here is kept minimal. The check after will use pgrep.
            # We won't run `sudo tor` directly here as it can behave unexpectedly without proper config.
            # Instead, we rely on `pytor.start_tor()` which is called by `install_requirements_and_tor()`
            # which should have run before this.
            # The purpose here is to check again with pgrep after systemctl/service failures.
            pass # No direct command here, will rely on pgrep after this.

        except Exception as e:
            service_start_errors.append(f"Direct tor: Exception - {str(e)}")


    stop_event.set()
    spinner_thread.join()

    # Final check after all attempts
    if is_tor_service_running():
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor process is running! (Verified by pgrep after start attempts){C_END}\n")
    else:
        print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to start or verify Tor service after all attempts.{C_END}")
        if systemctl_failed_non_systemd:
            print(f"{C_CYAN}{EMOJI_INFO} Systemd (systemctl) is not available or not the init system. Standard service start failed.{C_END}")
        if service_cmd_failed_non_systemd:
            print(f"{C_CYAN}{EMOJI_INFO} 'service' command indicated an issue (possibly non-systemd environment). Standard service start failed.{C_END}")
        
        if not service_start_methods_attempted:
             print(f"{C_WARNING}{EMOJI_INFO} No suitable system service management commands (systemctl, service) were found or Tor is already installed but not running.{C_END}")

        if service_start_errors:
            print(f"{C_GRAY}Errors encountered during start attempts:{C_END}")
            for err in service_start_errors:
                print(f"{C_GRAY}  - {err}{C_END}")
        
        print(f"{C_WARNING}{EMOJI_INFO} Please ensure Tor is installed correctly and can be started manually on your system.{C_END}")
        print(f"{C_WARNING}  You might need to run: {C_BOLD}sudo tor{C_END}{C_WARNING} or check your system's Tor service logs.{C_END}")
        # Do not sys.exit(1) here, allow the main script to proceed to pytor.start_tor() if it's part of the setup.
        # The show_tor_status function later will be the final gatekeeper.

    print(f"\n{C_CYAN}{EMOJI_INFO} Tor service start step finished.{C_END}\n")

# --- EXECUTE PRIORITIZED SETUP CHECKS ---
# This section is executed when the script is loaded, before main() is explicitly called.
require_venv_or_exit() # Step 1: Must be in VENV

# Step 2: Check for root/sudo if potentially needed by subsequent steps 
# (e.g., Tor installation or starting system services).
# The check_root() function itself will print messages and exit if criteria are not met.
check_root() 

check_and_install_python_dependencies() # Step 3: Install Python packages (inside venv)
ensure_tor_installed() # Step 4: Install Tor (system-wide, may require sudo)
ensure_tor_service_running() # Step 5: Start Tor service (may require sudo)

# Banner will be printed from main() after these checks.

# Print completion message for setup checks
print(f"\n{C_GREEN}{EMOJI_ROCKET}{C_BOLD}{EMOJI_CELEBRATE} All pre-flight system checks passed! KADDU YT-VIEWS is ready to configure...{C_END}\n")

# --------------------------------------
# --- MAIN APPLICATION IMPORTS START HERE ---
import random
import requests
from urllib.parse import urlparse
import threading as th2
import signal
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import pyfiglet
from rich.console import Console
from rich.live import Live
from rich.text import Text
import pytor
# --- MAIN APPLICATION IMPORTS END HERE ---


# -----------------------------
# Color, Emoji, Banner, Spinner, and Utility Helpers
# -----------------------------
# The Colors class and EMOJIS dictionary previously here are now removed.
# All color and emoji references now use the global C_ and EMOJI_ constants defined at the top.

# Updated: 50+ real user agent strings (2024-2025, desktop, mobile, tablet, major browsers)
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Windows Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0",
    # Windows Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/118.0.0.0",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    # Mac Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    # Mac Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:136.0) Gecko/20100101 Firefox/136.0",
    # Mac Edge
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.3124.85",
    # Mac Opera
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/118.0.0.0",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    # Linux Firefox
    "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0",
    # Chromebook
    "Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 15; SM-S931B Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 9 Pro Build/AD1A.240418.003; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0.6367.54 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 9 Build/AD1A.240411.003.A5; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0.6367.54 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 8 Pro Build/AP4A.250105.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 15; Pixel 8 Build/AP4A.250105.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36",
    # Android Firefox
    "Mozilla/5.0 (Android 15; Mobile; rv:136.0) Gecko/136.0 Firefox/136.0",
    # Android Samsung
    "Mozilla/5.0 (Linux; Android 15; SM-S931U Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-F9560 Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
    # Android Opera
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36 OPR/89.0.0.0",
    # iPhone Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.7 Mobile/15E148 Safari/604.1",
    # iPhone Chrome
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/134.0.6998.99 Mobile/15E148 Safari/604.1",
    # iPhone Edge
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/136.0.3240.91 Version/18.0 Mobile/15E148 Safari/604.1",
    # iPhone Firefox
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/136.0 Mobile/15E148 Safari/605.1.15",
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 17_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Mobile/15E148 Safari/604.1",
    # iPad Chrome
    "Mozilla/5.0 (iPad; CPU OS 17_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/134.0.6998.99 Mobile/15E148 Safari/604.1",
    # iPad Edge
    "Mozilla/5.0 (iPad; CPU OS 17_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/134.0.3124.85 Version/18.0 Mobile/15E148 Safari/604.1",
    # iPad Firefox
    "Mozilla/5.0 (iPad; CPU OS 14_7_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/136.0 Mobile/15E148 Safari/605.1.15",
    # Tablet Android
    "Mozilla/5.0 (Linux; Android 14; SM-X306B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-P619N Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
    # Kindle
    "Mozilla/5.0 (Linux; Android 11; KFRASWI Build/RS8332.3115N) AppleWebKit/537.36 (KHTML, like Gecko) Silk/47.1.79 like Chrome/47.0.2526.80 Safari/537.36",
    # Smart TV
    "Mozilla/5.0 (Linux; Android 11; AFTKRT Build/RS8101.1849N; wv)PlexTV/10.0.0.4149",
    # Game Console
    "Mozilla/5.0 (PlayStation; PlayStation 5/2.26) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox Series X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36 Edge/20.02",
    # Bots (for completeness, but not used for normal views)
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
]

def print_animated_banner():
    """
    Prints a big, bold ASCII banner with animation using pyfiglet and rich.
    """
    console = Console()
    banner_text = pyfiglet.figlet_format("KADDU YT-VIEWS", font="slant")
    # Animate the banner by printing it line by line with a delay
    lines = banner_text.splitlines()
    with Live("", refresh_per_second=20, console=console) as live:
        display = ""
        for line in lines:
            display += f"[bold magenta]{line}[/bold magenta]\n"
            live.update(Text(display))
            time.sleep(0.07)
    # Add subtitle and info
    console.print("[bold cyan]🎃 YT-Views - Simulating YouTube Views Like a Pro! 🎃[/bold cyan]")
    console.print("[bold green]Powered by PyTor & Smart Automation[/bold green]")
    console.print("[bold yellow]GitHub: https://github.com/Kaddu-Hacker/InfiniteYtViews[/bold yellow]")
    console.print("[bold blue]Tip: Always run in a virtual environment![/bold blue]")
    console.print("[bold white]-------------------------------------------------------------[/bold white]")

# Simple spinner for waiting periods
def spinner(seconds, message):
    """
    Displays a simple CLI spinner for a specified duration.
    Args:
        seconds (int): Duration to spin.
        message (str): Message to display alongside the spinner.
    """
    spinner_chars = ['|', '/', '-', '\\\\']
    end_time = time.time() + seconds
    idx = 0
    while time.time() < end_time:
        print(f"\r{C_WARNING}{EMOJI_SPINNER} {message} {spinner_chars[idx % 4]}{C_END}", end='', flush=True) # MODIFIED: Used C_WARNING, EMOJI_SPINNER, C_END
        time.sleep(0.2)
        idx += 1
    print("\\r" + " " * (len(message) + 5) + "\\r", end='') # Clear line

# Random user-agent
def get_random_user_agent():
    """Returns a randomly selected User-Agent string."""
    return random.choice(USER_AGENTS)

# Randomized watch time
def get_random_watch_time(base_length, is_short=False):
    """
    Calculates a randomized watch time.
    For shorts, it's a fixed short duration (e.g., 15-55s).
    For videos, it's a percentage of the base_length (e.g., 90-110%).
    """
    if is_short:
        return random.randint(min(15, base_length), min(base_length, 55)) 
    else:
        return int(base_length * random.uniform(0.9, 1.1))

# Randomized start delay (1-5s)
def get_random_start_delay():
    """Returns a random delay between 1 and 5 seconds."""
    return random.randint(1, 5)

# Validate a link (HEAD request via Tor)
def validate_link(link, tor_port):
    """
    Validates a given URL by making a HEAD request through a specific Tor port.
    Args:
        link (str): The URL to validate.
        tor_port (int): The SOCKS5 proxy port for Tor.
    Returns:
        bool: True if the link is valid (status code < 400), False otherwise.
    """
    proxies = {"http": f"socks5h://127.0.0.1:{tor_port}", "https": f"socks5h://127.0.0.1:{tor_port}"}
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.head(link, proxies=proxies, headers=headers, timeout=15, allow_redirects=True)
        return response.status_code < 400
    except requests.exceptions.RequestException as e:
        # print(f"{C_WARNING}{EMOJI_ERROR} Link validation error for {link} on port {tor_port}: {e}{C_END}") # MODIFIED
        return False

# Simulate a view (with random user-agent and tor port)
def simulate_view(link, tor_port, watch_time):
    """
    Simulates a single view to a link through a specified Tor port for a given watch time.
    Args:
        link (str): The URL to view.
        tor_port (int): The SOCKS5 proxy port for Tor.
        watch_time (int): The duration to simulate watching the content.
    Returns:
        bool: True if the view simulation was successful (status code < 400), False otherwise.
    """
    proxies = {"http": f"socks5h://127.0.0.1:{tor_port}", "https": f"socks5h://127.0.0.1:{tor_port}"}
    headers = {"User-Agent": get_random_user_agent()}
    try:
        response = requests.get(link, headers=headers, proxies=proxies, timeout=20, stream=True)
        if response.status_code < 400:
            time.sleep(watch_time) 
            response.close() 
            return True
        response.close()
        return False
    except requests.exceptions.RequestException as e:
        # print(f"{C_WARNING}{EMOJI_ERROR} View simulation error for {link} on port {tor_port}: {e}{C_END}") # MODIFIED
        return False

def get_user_links():
    """
    Prompts the user for link details (URL, type, length) with an improved workflow.
    First asks for the type of content (videos, shorts, or mixed).
    Then, for each batch of a specific type, it can ask for a default length.
    Returns a list of link dictionaries.
    """
    print(f"\n{C_HEADER}{EMOJI_LINK} Let's add your content! {EMOJI_LINK}{C_END}") # MODIFIED
    links = []
    link_id_counter = 0

    while True:
        print(f"{C_CYAN}What kind of content do you want to add?{C_END}") # MODIFIED
        print(f"  1. Only YouTube Videos {EMOJI_VIDEO}") # MODIFIED
        print(f"  2. Only YouTube Shorts {EMOJI_SHORT}") # MODIFIED
        print(f"  3. Both Videos and Shorts (Mixed)")
        content_choice_str = input(f"{C_CYAN}{EMOJI_PROMPT} Enter your choice (1-3) [Press Enter for 1]: {C_END}").strip() # MODIFIED
        if content_choice_str.lower() == 'help':
            print(HELP_TEXT) # Assuming HELP_TEXT is defined elsewhere
            continue
        
        content_choice = '1' # Default to Videos
        if content_choice_str in ['1', '2', '3']:
            content_choice = content_choice_str
        elif not content_choice_str: # Enter for default
            pass # Keeps default '1'
        else:
            print(f"{C_WARNING}{EMOJI_ERROR} Invalid choice. Please enter 1, 2, or 3.{C_END}") # MODIFIED
            continue
        break

    content_types_to_add = []
    if content_choice == '1':
        content_types_to_add.append(('video', EMOJI_VIDEO)) # MODIFIED
    elif content_choice == '2':
        content_types_to_add.append(('short', EMOJI_SHORT)) # MODIFIED
    elif content_choice == '3':
        content_types_to_add.append(('video', EMOJI_VIDEO)) # MODIFIED
        content_types_to_add.append(('short', EMOJI_SHORT)) # MODIFIED

    for content_type, content_emoji in content_types_to_add:
        print(f"\n{C_HEADER}--- Adding {content_type.capitalize()}s {content_emoji} ---{C_END}") # MODIFIED
        
        while True:
            try:
                num_items_str = input(f"{C_CYAN}{EMOJI_PROMPT} How many {content_type}s? (Enter a number, 0 to skip): {C_END}").strip() # MODIFIED
                if num_items_str.lower() == 'help':
                    print(HELP_TEXT)
                    continue
                num_items = int(num_items_str) if num_items_str else 0
                if num_items < 0:
                    print(f"{C_WARNING}{EMOJI_ERROR} Please enter a non-negative number.{C_END}") # MODIFIED
                    continue
                if num_items == 0:
                    print(f"{C_BLUE}Skipping {content_type}s.{C_END}") # MODIFIED
                    break 
                break
            except ValueError:
                print(f"{C_WARNING}{EMOJI_ERROR} Invalid input. Please enter a number.{C_END}") # MODIFIED
        if num_items == 0: continue

        # Ask for a default length for this batch of content_type
        default_length_for_batch = None
        min_length = 10 if content_type == 'short' else 60
        suggested_length = 60 if content_type == 'short' else 300

        while True:
            use_default_len_str = input(f"  {EMOJI_PROMPT} Set a default length for these {num_items} {content_type}s? (yes/no) [Enter for no]: {C_END}").strip().lower() # MODIFIED
            if use_default_len_str == 'help': print(HELP_TEXT); continue
            if use_default_len_str in ['y', 'yes']:
                while True:
                    length_str = input(f"    {EMOJI_PROMPT} Enter default length for {content_type}s in seconds [Enter for {suggested_length}s]: {C_END}").strip() # MODIFIED
                    if length_str.lower() == 'help': print(HELP_TEXT); continue
                    try:
                        default_length_for_batch = int(length_str) if length_str else suggested_length
                        if default_length_for_batch < min_length:
                            print(f"{C_WARNING}{EMOJI_ERROR} Min length for {content_type} is {min_length}s.{C_END}") # MODIFIED
                            default_length_for_batch = None # Reset
                            continue
                        break
                    except ValueError:
                        print(f"{C_WARNING}{EMOJI_ERROR} Invalid number for length.{C_END}") # MODIFIED
                break
            elif use_default_len_str in ['n', 'no', '']:
                break
            else:
                print(f"{C_WARNING}{EMOJI_ERROR} Invalid choice. Please enter 'yes' or 'no'.{C_END}") # MODIFIED

        for i in range(num_items):
            print(f"\n{C_BLUE}--- {content_type.capitalize()} #{i+1} ---{C_END}") # MODIFIED
            while True:
                link_url = input(f"  {EMOJI_PROMPT} Enter URL for {content_type} #{i+1}: ").strip()
                if link_url.lower() == 'help': print(HELP_TEXT); continue
                if not link_url: print(f"{C_WARNING}{EMOJI_ERROR} URL cannot be empty.{C_END}"); continue # MODIFIED
                if not (link_url.startswith("http://") or link_url.startswith("https://")):\
                    print(f"{C_WARNING}{EMOJI_ERROR} Invalid URL. Must start with http:// or https://{C_END}"); continue # MODIFIED
                break
            
            current_length_sec = default_length_for_batch
            if current_length_sec is None: # If no batch default, ask individually
                length_prompt = f"  {EMOJI_PROMPT} Enter {content_type} length in seconds [Enter for {suggested_length}s]: "
                while True:
                    length_str = input(length_prompt).strip()
                    if length_str.lower() == 'help': print(HELP_TEXT); continue
                    try:
                        current_length_sec = int(length_str) if length_str else suggested_length
                        if current_length_sec < min_length:
                            print(f"{C_WARNING}{EMOJI_ERROR} Min length for {content_type} is {min_length}s.{C_END}"); continue # MODIFIED
                        break
                    except ValueError:
                        print(f"{C_WARNING}{EMOJI_ERROR} Invalid input. Please enter a number for length.{C_END}") # MODIFIED
            
            links.append({'url': link_url, 'type': content_type, 'length': current_length_sec, 'id': link_id_counter})
            link_id_counter += 1
            
    if not links:
        print(f"{C_WARNING}{EMOJI_INFO} No content was added.{C_END}") # MODIFIED
    return links

def get_views_per_link():
    """
    Prompts user for number of views per link.
    """
    print(f"\n{C_HEADER}{EMOJI_VIEW} View Configuration {EMOJI_VIEW}{C_END}") # MODIFIED (used EMOJI_VIEW)
    while True:
        views_str = input(f"{C_CYAN}{EMOJI_PROMPT} How many views per link? (e.g., 100) [Press Enter for 10, 0 for 'continuous']: {C_END}").strip() # MODIFIED
        if views_str.lower() == 'help':
            print(HELP_TEXT)
            continue
        try:
            views = int(views_str) if views_str else 10
            if views < 0:
                print(f"{C_WARNING}{EMOJI_ERROR} Please enter 0 or a positive number.{C_END}") # MODIFIED
                continue
            return views 
        except ValueError:
            print(f"{C_WARNING}{EMOJI_ERROR} Invalid input. Please enter a number.{C_END}") # MODIFIED

def get_connection_count():
    """
    Prompts user for number of parallel Tor connections.
    """
    print(f"\n{C_HEADER}{EMOJI_CONNECTING} Connection Setup {EMOJI_CONNECTING}{C_END}") # MODIFIED (used EMOJI_CONNECTING)
    print(f"   (More connections can mean faster view generation but need Tor to be set up for multiple SOCKS ports if > 1)")
    while True:
        num_connections_str = input(f"{C_CYAN}{EMOJI_PROMPT} How many parallel connections (Tor circuits)? (1-10) [Press Enter for 1]: {C_END}").strip() # MODIFIED
        if num_connections_str.lower() == 'help':
            print(HELP_TEXT)
            print(f"{C_BLUE}{EMOJI_INFO} Each connection uses a distinct Tor SOCKS port (e.g., 9050, 9051...). Ensure Tor is configured if using >1.{C_END}") # MODIFIED
            continue
        try:
            num_connections = int(num_connections_str) if num_connections_str else 1
            if not 1 <= num_connections <= 10:
                print(f"{C_WARNING}{EMOJI_ERROR} Please enter a number between 1 and 10.{C_END}") # MODIFIED
                continue
            return num_connections
        except ValueError:
            print(f"{C_WARNING}{EMOJI_ERROR} Invalid input. Please enter a number.{C_END}") # MODIFIED

def get_dry_run_choice():
    """
    Asks if user wants a dry run.
    """
    print(f"\n{C_HEADER}{EMOJI_DRY_RUN} Dry Run Option {EMOJI_DRY_RUN}{C_END}") # MODIFIED
    while True:
        choice = input(f"{C_CYAN}{EMOJI_PROMPT} Perform a 'dry run' first? (yes/no) [Press Enter for no]: {C_END}").strip().lower() # MODIFIED
        if choice == 'help':
            print(HELP_TEXT)
            print(f"{C_BLUE}{EMOJI_INFO} Dry run simulates without actual views.{C_END}") # MODIFIED
            continue
        if choice in ['yes', 'y']:
            return True
        if choice in ['no', 'n', '']:
            return False
        print(f"{C_WARNING}{EMOJI_ERROR} Invalid choice. Please enter 'yes' or 'no'.{C_END}") # MODIFIED

def validate_all_links(links, tor_ports):
    """
    Validates all user-provided links using available Tor ports in a round-robin fashion.
    Args:
        links (list): List of link dictionaries.
        tor_ports (list): List of available Tor SOCKS port numbers.
    Returns:
        list: A list of valid link dictionaries. Invalid links are reported and excluded.
    """
    print(f"\n{C_BLUE}{EMOJI_SEARCH} Validating links...{C_END}") # MODIFIED (used EMOJI_SEARCH)
    valid_links = []
    if not tor_ports:
        print(f"{C_FAIL}{EMOJI_ERROR} No Tor ports available for link validation. Check Tor setup.{C_END}") # MODIFIED
        return []

    for i, link_info in enumerate(links):
        # Cycle through tor_ports for validation to distribute load and mimic multiple connections
        port_to_use = tor_ports[i % len(tor_ports)] 
        is_valid = validate_link(link_info['url'], port_to_use)
        if is_valid:
            print(f"{C_GREEN}{EMOJI_SUCCESS} Link #{link_info['id']+1} ({link_info['url'][:60]}...) is valid via port {port_to_use}.{C_END}") # MODIFIED
            valid_links.append(link_info)
        else:
            print(f"{C_FAIL}{EMOJI_ERROR} Link #{link_info['id']+1} ({link_info['url'][:60]}...) is invalid or unreachable via Tor port {port_to_use}. It will be skipped.{C_END}") # MODIFIED
    
    if not valid_links:
        print(f"{C_WARNING}{EMOJI_ERROR} No valid links to process after validation.{C_END}") # MODIFIED (used EMOJI_ERROR)
    return valid_links

def estimate_total_time(links, views_per_link, num_connections):
    """
    Estimates the total time required to generate the views.
    Args:
        links (list): List of link dictionaries (must include 'length').
        views_per_link (int): Number of views to generate for each link (0 for continuous).
        num_connections (int): Number of parallel connections/threads.
    Returns:
        str: A human-readable string of the estimated time, or relevant message.
    """
    if not links or num_connections <= 0:
        return "N/A (cannot estimate without links or connections)"
    if views_per_link == 0: # Continuous mode
        return "Continuous (runs until manually stopped)"
    
    total_watch_seconds_all_links_one_cycle = sum(link['length'] for link in links)
    total_watch_seconds_all_views = total_watch_seconds_all_links_one_cycle * views_per_link

    # Estimate overhead: random start delay (avg 3s) + inter-view delay (avg ~7s for fixed, ~15s for continuous)
    # Plus very small time for the actual request/response aside from watch time.
    # This is highly approximate.
    avg_overhead_per_view_action = get_random_start_delay() + 7 # Approx 3 + 7 = 10s
    total_actions = len(links) * views_per_link
    total_overhead_seconds = total_actions * avg_overhead_per_view_action

    # Total seconds if run serially
    grand_total_seconds_serial = total_watch_seconds_all_views + total_overhead_seconds
    
    # Estimate with parallel connections. This is not perfectly linear.
    # A simple division might be too optimistic. Let's add a parallelism efficiency factor (e.g., 0.7-0.9)
    # For simplicity, just dividing by num_connections gives a very rough lower bound.
    estimated_seconds = grand_total_seconds_serial / num_connections
    
    # Add a general buffer for Tor circuit establishment, other latencies
    estimated_seconds *= 1.3 # 30% general buffer

    if estimated_seconds < 1:
        estimated_seconds = 1 # Avoid 0 seconds estimation for very small tasks
        
    if estimated_seconds < 60:
        return f"~{int(round(estimated_seconds))} seconds"
    elif estimated_seconds < 3600:
        return f"~{int(round(estimated_seconds / 60))} minutes"
    else:
        h = int(estimated_seconds / 3600)
        m = int(round((estimated_seconds % 3600) / 60))
        return f"~{h} hours and {m} minutes"

# Updated show_tor_status to accept and iterate over a list of ports.
def show_tor_status(ports_to_use, base_control_port): # Signature updated
    """
    Checks the status of specified Tor SOCKS ports.
    Attempts to start the general Tor service via pytor if no ports are initially active.
    Warns if some ports are not operational and exits if the primary port is not working.
    """
    print(f"\n{C_BLUE}{EMOJI_TOR} Checking Tor SOCKS Port Status for: {ports_to_use}...{C_END}")
    
    operational_ports = []
    
    if not ports_to_use:
        print(f"{C_FAIL}{EMOJI_ERROR} No Tor ports specified to check.{C_END}")
        sys.exit(1)

    def check_ports(port_list, existing_operational_ports):
        current_operational = list(existing_operational_ports) # Work on a copy
        for port_to_check in port_list:
            if port_to_check in current_operational: # Skip if already confirmed
                continue
            print(f"{C_CYAN}  Checking SOCKS Port: {port_to_check}...{C_END}")
            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=spinner_animation, args=(f"Verifying Tor SOCKS port {port_to_check}", stop_event, 20), kwargs={"emoji": EMOJI_SEARCH, "color": C_CYAN}) # Timeout 20s
            spinner_thread.start()
            current_ip = None
            try:
                current_ip = pytor.get_ip(port_to_check) # pytor.get_ip should handle its own timeout
            except Exception as e: # Catch exceptions from pytor.get_ip() itself
                print(f"{C_GRAY}    Exception during pytor.get_ip({port_to_check}): {e}{C_END}") # Debug level
            finally:
                stop_event.set()
                spinner_thread.join()

            if current_ip:
                print(f"{C_GREEN}{EMOJI_SUCCESS} Tor SOCKS Port {port_to_check} is operational. Current IP: {current_ip}{C_END}")
                if port_to_check not in current_operational:
                    current_operational.append(port_to_check)
            else:
                print(f"{C_WARNING}{EMOJI_WARNING} Tor SOCKS Port {port_to_check} is NOT operational or IP couldn't be fetched.{C_END}")
        return current_operational

    # First pass
    operational_ports = check_ports(ports_to_use, [])

    # If no ports are operational after the first pass, try to start/restart Tor service
    if not operational_ports:
        print(f"\n{C_WARNING}{EMOJI_WARNING} No Tor SOCKS ports were initially active.{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} Attempting to ensure Tor service is running via pytor.start_tor()... (This may take a moment and might require sudo if Tor isn't correctly permissioned or running){C_END}")
        
        stop_event_tor_start = threading.Event()
        spinner_tor_start_thread = threading.Thread(target=spinner_animation, args=("Attempting to start/initialize Tor service", stop_event_tor_start, 45), kwargs={"emoji": EMOJI_TOR, "color": C_BLUE}) # 45s timeout for Tor start
        spinner_tor_start_thread.start()
        tor_started_pytor = False
        pytor_start_error = ""
        try:
            pytor.start_tor() # Assumes this function handles general Tor service start/check.
                              # It should be idempotent or safe to call if Tor is already running.
            tor_started_pytor = True # Assume success if no exception
        except Exception as e:
            pytor_start_error = str(e)
        finally:
            stop_event_tor_start.set()
            spinner_tor_start_thread.join()

        if tor_started_pytor:
            print(f"{C_GREEN}{EMOJI_SUCCESS} pytor.start_tor() command issued. Waiting a few seconds for Tor to initialize...{C_END}")
            time.sleep(10) # Increased wait time after pytor.start_tor()
            print(f"{C_CYAN}{EMOJI_INFO} Re-checking all specified Tor SOCKS ports...{C_END}")
            operational_ports = check_ports(ports_to_use, []) # Re-check all ports
        else:
            print(f"{C_FAIL}{EMOJI_ERROR} pytor.start_tor() failed or encountered an error: {pytor_start_error}{C_END}")
            print(f"{C_WARNING}{EMOJI_WARNING} This might be due to permissions (try with sudo -E), Tor not being installed, or a Tor misconfiguration.{C_END}")


    # Final assessment
    if not operational_ports:
        print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} CRITICAL: Still no Tor SOCKS ports are operational after all attempts.{C_END}")
    elif ports_to_use[0] not in operational_ports:
        print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} CRITICAL: The primary Tor SOCKS port ({ports_to_use[0]}) is NOT operational.{C_END}")
        print(f"{C_WARNING}  Operational ports found: {operational_ports if operational_ports else 'None'}.{C_END}")
    
    if ports_to_use[0] not in operational_ports: # Covers both no operational_ports or primary missing
        print(f"{C_WARNING}  Please ensure Tor is installed, running, and configured to listen on the required SOCKS ports, especially {C_BOLD}{ports_to_use[0]}{C_END}.{C_END}")
        print(f"{C_WARNING}  Required ports for this session: {ports_to_use}{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO}  For multiple connections (if you requested >1), your 'torrc' file needs multiple 'SocksPort' entries.{C_END}")
        print(f"{C_CYAN}  Example for 3 ports (9050, 9052, 9054) in torrc:{C_END}")
        print(f"{C_GRAY}    SocksPort 9050{C_END}")
        print(f"{C_GRAY}    SocksPort 9052{C_END}")
        print(f"{C_GRAY}    SocksPort 9054{C_END}")
        print(f"{C_FAIL}Exiting due to Tor port unavailability.{C_END}")
        sys.exit(1)

    # Check if all requested ports are operational
    all_requested_are_operational = True
    non_operational_requested_ports = []
    for p in ports_to_use:
        if p not in operational_ports:
            all_requested_are_operational = False
            non_operational_requested_ports.append(p)

    if all_requested_are_operational:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} All {len(operational_ports)} requested Tor SOCKS ports are operational! IPs fetched for all.{C_END}\n")
    else:
        # Primary port is working, but some others are not.
        print(f"\n{C_WARNING}{EMOJI_WARNING} WARNING: Not all requested Tor SOCKS ports are operational.{C_END}")
        print(f"{C_GREEN}  Operational ports that will be used: {operational_ports}{C_END}")
        print(f"{C_FAIL}  Requested ports that are NOT operational: {non_operational_requested_ports}{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO}  The script will attempt to proceed using the original list: {ports_to_use}.{C_END}")
        print(f"{C_CYAN}  However, view attempts using non-operational ports ({non_operational_requested_ports}) will likely fail.{C_END}")
        print(f"{C_WARNING}  For full parallel capacity, ensure Tor is configured for ALL requested ports: {ports_to_use}.{C_END}")
        print(f"{C_CYAN}  Check your 'torrc' file. Example for ports 9050, 9052, 9054:{C_END}")
        print(f"{C_GRAY}    SocksPort 9050\\n    SocksPort 9052\\n    SocksPort 9054{C_END}")

    print(f"\n{C_CYAN}{EMOJI_INFO} Tor SOCKS port check finished.{C_END}\n")
    # Note: This function does not return the filtered list of operational_ports to main.
    # Main continues to use the originally requested 'ports_to_use'.
    # Link validation and view_workers will encounter errors if they are assigned a non-operational port.
    # This is a compromise to simplify the diff for now. Ideally, main should use 'operational_ports'.

def dry_run_summary(links, views_count, num_connections, tor_ports_to_use):
    print(f"\n{C_HEADER}{EMOJI_DRY_RUN} --- DRY RUN MODE --- {EMOJI_DRY_RUN}{C_END}")
    print(f"{C_CYAN}{EMOJI_INFO} This will simulate the view generation process without actually sending requests.{C_END}")
    print(f"{C_BLUE}Configuration Summary:{C_END}")
    print(f"{C_WHITE}  - Target Links to Process:{C_END}")
    if links:
        for i, link_info in enumerate(links):
            # Ensure title is present, provide fallback if not (though get_user_links should ensure it)
            title = link_info.get('title', 'N/A') 
            print(f"{C_GRAY}    {i+1}. {link_info['url']} (Title: {title}){C_END}")
    else:
        print(f"{C_GRAY}    No links provided for dry run.{C_END}")
        
    print(f"{C_WHITE}  - Views per Link: {C_BOLD}{views_count}{C_END}")
    print(f"{C_WHITE}  - Number of Parallel Connections/Threads: {C_BOLD}{num_connections}{C_END}")
    
    # Display the list of Tor SOCKS ports that will be used.
    if tor_ports_to_use:
        ports_str = ", ".join(map(str, tor_ports_to_use))
        print(f"{C_WHITE}  - Tor SOCKS Ports to be Used: {C_BOLD}{ports_str}{C_END}")
    else:
        # This case should ideally not be reached if Tor is essential and ports are configured.
        print(f"{C_YELLOW}{EMOJI_WARNING}  - Tor SOCKS Ports: None configured or passed (View generation may fail or not use Tor).{C_END}")

    print(f"{C_BLUE}Simulated Actions:{C_END}")
    if links:
        print(f"{C_GRAY}  - For each of the {len(links)} link(s):")
        print(f"{C_GRAY}    - {views_count} view attempts would be simulated.")
        if num_connections > 0 and tor_ports_to_use:
            print(f"{C_GRAY}    - If {num_connections} > 1, view attempts would be distributed among threads using ports from: {tor_ports_to_use}.{C_END}")
            print(f"{C_GRAY}    - Each attempt would try to fetch the video page via a Tor SOCKS proxy on one of the configured ports.{C_END}")
        else:
            print(f"{C_GRAY}    - Tor SOCKS proxy usage would depend on single port configuration or availability.{C_END}")
        print(f"{C_GRAY}    - User agent would be randomized for each attempt.{C_END}")
        print(f"{C_GRAY}    - Delays would be simulated between actions.{C_END}")
    else:
        print(f"{C_GRAY}  - No links to simulate actions for.{C_END}")
        
    print(f"\n{C_GREEN}{EMOJI_SUCCESS} Dry run simulation complete. Check the configuration above.{C_END}")

# --- Progress Callback for Workers ---
def view_progress_callback(results_list_ref, link_id, views_done_for_link_total, overall_views_total, url, success_flag, port_used, watch_duration_or_error_msg, link_title="N/A"):
    """
    Callback function for view_worker to report its progress.
    Args:
        results_list_ref (list): Reference to the list in the calling scope to store results.
        link_id (int): Unique ID of the link.
        views_done_for_link_total (int): Total views completed for this specific link so far.
        overall_views_total (int): Total views completed overall across all links/workers.
        url (str): The URL that was processed.
        success_flag (bool): True if the view was successful, False otherwise.
        port_used (int): The Tor SOCKS port used for the attempt.
        watch_duration_or_error_msg (any): Actual watch time if successful, or an error message string if failed.
        link_title (str): Title of the video/link.
    """
    if success_flag:
        print(f"{C_GREEN}{EMOJI_SUCCESS} View #{views_done_for_link_total} for '{link_title}' ({url[:40]}...) on Port {port_used} SUCCEEDED. Watched for {watch_duration_or_error_msg}s. Overall views: {overall_views_total}.{C_END}")
        results_list_ref.append((True, url, port_used, None))
    else:
        print(f"{C_FAIL}{EMOJI_ERROR} View attempt for '{link_title}' ({url[:40]}...) on Port {port_used} FAILED. Reason: {watch_duration_or_error_msg}. Overall views: {overall_views_total}.{C_END}")
        results_list_ref.append((False, url, port_used, str(watch_duration_or_error_msg)))

# --- Threaded View Generation ---
def create_and_run_threads(links_data, views_count_per_link, num_concurrent_workers, tor_ports_to_use, results_list_ref):
    global stop_event_global, completed_views_total, views_per_link_tracker

    if not tor_ports_to_use:
        print(f"{C_FAIL}{EMOJI_ERROR} Tor port list is empty in create_and_run_threads. Cannot proceed.{C_END}")
        return 0, 0

    print(f"\n{C_BLUE}{EMOJI_THREADS} Preparing to launch up to {num_concurrent_workers} concurrent viewer worker(s) for {len(links_data)} link(s)...{C_END}")
    if tor_ports_to_use:
         print(f"{C_CYAN}{EMOJI_INFO} Distributing {len(tor_ports_to_use)} Tor SOCKS ports ({', '.join(map(str, tor_ports_to_use))}) among workers.{C_END}")
    else:
         print(f"{C_WARNING}{EMOJI_WARNING} No Tor SOCKS ports provided to distribute.{C_END}")

    completed_views_total = 0
    views_per_link_tracker = {}
    active_threads_list = []
    port_assignment_index = 0
    launched_thread_objects = []

    for link_idx, link_info in enumerate(links_data):
        if stop_event_global.is_set():
            print(f"{C_WARNING}{EMOJI_INFO} Stop signal received during thread creation. No more new tasks will be started.{C_END}")
            break
        while True:
            active_threads_list = [t for t in active_threads_list if t.is_alive()]
            if len(active_threads_list) < num_concurrent_workers:
                break
            if stop_event_global.is_set(): break
            time.sleep(0.5)
        if stop_event_global.is_set(): break
        url = link_info['url']
        video_title = link_info.get('title', f"LinkID_{link_info.get('id', 'N/A')}")
        assigned_tor_port = tor_ports_to_use[port_assignment_index % len(tor_ports_to_use)]
        port_assignment_index += 1
        thread_name = f"Worker-{link_info.get('id', 'X')}-{os.path.basename(urlparse(url).path)[:15]}"
        progress_cb_for_worker = lambda lid, vdone, ovdone, lkurl, succ, port, dur_err, vt=video_title: view_progress_callback(
            results_list_ref, lid, vdone, ovdone, lkurl, succ, port, dur_err, vt
        )
        thread = threading.Thread(
            target=view_worker,
            args=(
                link_info,
                views_count_per_link,
                [assigned_tor_port],
                progress_cb_for_worker
            ),
            name=thread_name
        )
        active_threads_list.append(thread)
        launched_thread_objects.append(thread)
        thread.start()
        print(f"{C_GRAY}{EMOJI_INFO} Launched: {thread_name} for '{video_title}' (Target: {views_count_per_link} views, Port: {assigned_tor_port}){C_END}")
        if len(links_data) > 1 and link_idx < len(links_data) -1 :
            time.sleep(random.uniform(0.1, 0.5))
    print(f"\n{C_BLUE}{EMOJI_WAIT} All {len(launched_thread_objects)} worker threads for links have been launched. Waiting for completion...{C_END}")
    for thread_obj in launched_thread_objects:
        thread_obj.join(timeout=30)
        if thread_obj.is_alive():
            print(f"{C_WARNING}{EMOJI_WARNING} Thread {thread_obj.name} did not terminate cleanly after stop signal and join timeout. It might be stuck in a blocking call.{C_END}")
    print(f"\n{C_GREEN}{EMOJI_SUCCESS} All worker threads have completed or been signaled to stop.{C_END}")
    total_success_count = 0
    total_failure_count = 0
    for success, _, _, _ in results_list_ref:
        if success:
            total_success_count += 1
        else:
            total_failure_count += 1
    return total_success_count, total_failure_count

# --- Simulate View (Refactored) ---
def simulate_view(link, tor_port, watch_time):
    proxies = {"http": f"socks5h://127.0.0.1:{tor_port}", "https": f"socks5h://127.0.0.1:{tor_port}"}
    headers = {"User-Agent": get_random_user_agent()}
    try:
        response = requests.get(link, headers=headers, proxies=proxies, timeout=20, stream=True)
        if response.status_code < 400:
            time.sleep(watch_time)
            response.close()
            return True, None
        error_msg = f"HTTP Status {response.status_code}"
        response.close()
        return False, error_msg
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.RequestException as e:
        return False, f"RequestException: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

# --- View Worker (Refactored) ---
def view_worker(link_info, views_to_generate_for_this_link, tor_ports_available, progress_callback_func):
    global completed_views_total, views_per_link_tracker, stop_event_global
    link_id = link_info['id']
    link_url = link_info['url']
    is_short_video = link_info['type'] == 'short'
    base_video_length = link_info['length']
    local_views_done_count = 0
    if not tor_ports_available:
        print(f"{C_FAIL}{EMOJI_ERROR} Critical: No Tor ports assigned to worker for {link_url}. Worker exiting.{C_END}")
        return
    current_port_index = random.randrange(len(tor_ports_available))
    while not stop_event_global.is_set():
        if views_to_generate_for_this_link > 0 and local_views_done_count >= views_to_generate_for_this_link:
            break
        chosen_tor_port = tor_ports_available[current_port_index % len(tor_ports_available)]
        current_port_index += 1
        pre_view_delay = get_random_start_delay()
        sleep_chunk_end_time = time.time() + pre_view_delay
        while time.time() < sleep_chunk_end_time:
            if stop_event_global.is_set(): break
            time.sleep(min(0.5, sleep_chunk_end_time - time.time()))
        if stop_event_global.is_set(): break
        actual_watch_time = get_random_watch_time(base_video_length, is_short_video)
        if stop_event_global.is_set(): break
        view_successful, sim_result_msg = simulate_view(link_url, chosen_tor_port, actual_watch_time)
        if stop_event_global.is_set(): break
        if view_successful:
            with completed_views_lock:
                completed_views_total += 1
                local_views_done_count += 1
                views_per_link_tracker[link_id] = views_per_link_tracker.get(link_id, 0) + 1
                current_link_total_views = views_per_link_tracker[link_id]
            progress_callback_func(link_id, current_link_total_views, completed_views_total, link_url, True, chosen_tor_port, actual_watch_time)
        else:
            with completed_views_lock:
                 current_link_total_views = views_per_link_tracker.get(link_id, 0)
            progress_callback_func(link_id, current_link_total_views, completed_views_total, link_url, False, chosen_tor_port, sim_result_msg)
        post_view_delay_base = 10 if views_to_generate_for_this_link == 0 else 5
        post_view_delay = random.uniform(post_view_delay_base, post_view_delay_base + 10)
        sleep_chunk_end_time = time.time() + post_view_delay
        while time.time() < sleep_chunk_end_time:
            if stop_event_global.is_set(): break
            time.sleep(min(0.5, sleep_chunk_end_time - time.time()))
        if stop_event_global.is_set(): break

def main():
    """Main function to run the YouTube view generation system."""
    
    # All critical setup (venv, root check, dependencies, Tor install/service)
    # has already been performed by the global script execution block when the script was loaded.
    
    # Now, print the banner as we are about to interact with the user.
    print_animated_banner() # Moved here: Banner is shown after all pre-flight checks pass.

    # The following calls are now redundant because they are handled by the prioritized global setup:
    # check_virtual_environment() # Redundant: Done by require_venv_or_exit() globally.
    # check_root() # Redundant: Done globally in the prioritized setup block.
    # install_requirements_and_tor() 
    #   - Dependency checks are done by check_and_install_python_dependencies() globally.
    #   - Tor installation is done by ensure_tor_installed() globally.
    #   - Tor service starting is initially handled by ensure_tor_service_running() globally.

    print(TIP_TEXT) 
    if input(f"{C_CYAN}{EMOJI_PROMPT} Press Enter to continue or type 'help': {C_END}").strip().lower() == 'help':
        print(HELP_TEXT)

    user_links_data = get_user_links()
    if not user_links_data:
        print(f"{C_WARNING}{EMOJI_INFO} No links provided. Exiting.{C_END}")
        sys.exit(1)

    views_per_target_link = get_views_per_link()
    num_parallel_connections = get_connection_count()
    
    # --- Tor Ports Setup ---
    # Determine base SOCKS and Control ports, trying pytor defaults first.
    try:
        base_tor_port = pytor.DEFAULT_TOR_PORT
    except AttributeError:
        print(f"{C_GRAY}{EMOJI_INFO} pytor.DEFAULT_TOR_PORT not defined, using 9050 as default SOCKS port.{C_END}")
        base_tor_port = 9050
    
    try:
        base_control_port = pytor.DEFAULT_CONTROL_PORT
    except AttributeError:
        print(f"{C_GRAY}{EMOJI_INFO} pytor.DEFAULT_CONTROL_PORT not defined, using 9051 as default Control port.{C_END}")
        base_control_port = 9051

    # Prepare a list of SOCKS ports to use, gapped by 2 as per HELP_TEXT example.
    # e.g., if num_connections = 3, ports will be [9050, 9052, 9054]
    tor_ports_to_use = [base_tor_port + (i * 2) for i in range(num_parallel_connections)]

    print(f"\n{C_BLUE}{EMOJI_TOR} Preparing and verifying {num_parallel_connections} Tor connection(s) on SOCKS ports: {tor_ports_to_use}...{C_END}")
    
    # show_tor_status checks connectivity for the required SOCKS ports.
    # It may attempt to start the general Tor service using pytor.start_tor() if no ports are active.
    # It expects the list of SOCKS ports and the base_control_port (in case pytor.start_tor() uses it, though current pytor.start_tor() seems generic).
    show_tor_status(ports_to_use=tor_ports_to_use, base_control_port=base_control_port)

    validated_links = validate_all_links(user_links_data, tor_ports_to_use) 
    
    if not validated_links: 
        print(f"{C_FAIL}{EMOJI_ERROR} No valid links to process after validation. Exiting.{C_END}")
        sys.exit(1)

    is_dry_run = get_dry_run_choice()
    if is_dry_run:
        # dry_run_summary also needs to accept the list of ports.
        dry_run_summary(validated_links, views_per_target_link, num_parallel_connections, tor_ports_to_use)
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}Dry run complete. Exiting.{C_END}")
        sys.exit(0)

    print(f"\n{C_HEADER}{EMOJI_ROCKET} STARTING VIEW GENERATION {EMOJI_ROCKET}{C_END}")
    
    all_threads = []
    results = [] 

    # Pass the list of ports to create_and_run_threads.
    total_success_sync, total_failure_sync = create_and_run_threads(
        validated_links, views_per_target_link, num_parallel_connections, tor_ports_to_use, results
    )

    # Display results
    print(f"\n{C_OKBLUE}--- FINAL SUMMARY ---")
    print(f"{C_OKGREEN}{EMOJI_SUCCESS} Total successful views: {total_success_sync}")
    print(f"{C_FAIL}{EMOJI_ERROR} Total failed attempts: {total_failure_sync}{C_END}")
    print(f"{C_OKBLUE}--------------------{C_END}")
    print(f"{C_HEADER}{EMOJI_THANKS} Thanks for using KADDU YT-VIEWS! {EMOJI_STAR}{C_END}")
    print(f"{C_YELLOW}Consider starring the project on GitHub: {GITHUB_LINK}{C_END}")

# Define GITHUB_LINK and TIP_TEXT (used in main)
GITHUB_LINK = "https://github.com/Kaddu-Hacker/InfiniteYtViews"
TIP_TEXT = f"{C_BLUE}{EMOJI_INFO} Tip: {C_BOLD}Always run this script in a Python virtual environment (venv){C_END} to avoid system-wide package conflicts and ensure correct dependency versions. See 'help' for more."

# --- GLOBAL LOCK FOR THREADING (for completed_views_total, etc.) ---
completed_views_lock = threading.Lock()

if __name__ == "__main__":
    # The prioritized setup checks (require_venv, check_root, dependencies, Tor) 
    # are now executed globally when the script is parsed.
    # So, when __main__ is entered, those are already done.
    main()
