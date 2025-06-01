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

C_HEADER = '\033[95m'
C_BLUE = '\033[94m'
C_CYAN = '\033[96m'
C_GREEN = '\033[92m'
C_WARNING = '\033[93m'
C_FAIL = '\033[91m'
C_END = '\033[0m'
C_BOLD = '\033[1m'
C_GRAY = '\033[90m'

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
def print_animated_banner():
    try:
        import pyfiglet
        from rich.console import Console
        from rich.live import Live
        from rich.text import Text
    except ImportError:
        print(f"{C_WARNING}{EMOJI_WARNING} Banner dependencies missing. Skipping banner animation.{C_END}")
        return
    console = Console()
    # Load custom ASCII art from file
    ascii_art_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ASCII')
    ascii_art_lines = []
    if os.path.exists(ascii_art_path):
        with open(ascii_art_path, 'r', encoding='utf-8') as f:
            ascii_art_lines = f.readlines()
    # Prepare big 'KADDU' ASCII text
    kaddu_text = pyfiglet.figlet_format("KADDU", font="big")
    kaddu_lines = kaddu_text.splitlines()
    # Animate custom ASCII art
    with Live("", refresh_per_second=20, console=console) as live:
        display = ""
        for line in ascii_art_lines:
            display += f"[bold green]{line.rstrip()}[/bold green]\n"
            live.update(Text(display))
            time.sleep(0.03)
        # Animate big 'KADDU' below the art
        for line in kaddu_lines:
            display += f"[bold magenta]{line}[/bold magenta]\n"
            live.update(Text(display))
            time.sleep(0.09)
    # Subheading and sub-subheading
    console.print("[bold cyan]YouTube Views Generator[/bold cyan]", style="bold underline")
    console.print("[bold green]100% Free & Open Source[/bold green]")
    console.print("[bold yellow]GitHub: https://github.com/Kaddu-Hacker/InfiniteYtViews[/bold yellow]")
    console.print("[bold blue]Tip: Always run in a virtual environment![/bold blue]")
    console.print("[bold white]-------------------------------------------------------------[/bold white]")

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
            install_cmd = ["sudo", "apt", "update", "-y"]
            install_cmd2 = ["sudo", "apt", "install", "tor", "-y"]
        elif is_command_available("yum"):
            installer = "yum"
            install_cmd = ["sudo", "yum", "install", "tor", "-y"]
        elif is_command_available("pacman"):
            installer = "pacman"
            install_cmd = ["sudo", "pacman", "-S", "--noconfirm", "tor"]
        if installer:
            print(f"\n{C_CYAN}{EMOJI_PROMPT} Installing Tor using '{installer}'...{C_END}")
            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=spinner_animation, args=(f"Installing Tor...", stop_event), kwargs={"emoji": EMOJI_TOR, "color": C_CYAN})
            spinner_thread.start()
            try:
                if installer == "apt":
                    proc1 = subprocess.run(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
                    proc2 = subprocess.run(install_cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
                    success = proc1.returncode == 0 and proc2.returncode == 0
                else:
                    proc = subprocess.run(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
                    success = proc.returncode == 0
                stop_event.set()
                spinner_thread.join()
                if success and is_command_available("tor"):
                    print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor installed successfully!{C_END}\n")
                else:
                    print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to install Tor!{C_END}")
                    if installer == "apt":
                        print(proc1.stderr.decode(errors='ignore'))
                        print(proc2.stderr.decode(errors='ignore'))
                    else:
                        print(proc.stderr.decode(errors='ignore'))
                    print(f"{C_WARNING}{EMOJI_INFO} Please install Tor manually using 'sudo apt install tor -y' or your system's package manager, then re-run this script.{C_END}")
                    sys.exit(1)
            except subprocess.TimeoutExpired:
                stop_event.set()
                spinner_thread.join()
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Tor installation timed out!{C_END}")
                sys.exit(1)
            except Exception as e:
                stop_event.set()
                spinner_thread.join()
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Exception during Tor installation: {e}{C_END}")
                print(f"{C_WARNING}{EMOJI_INFO} Please install Tor manually using 'sudo apt install tor -y' or your system's package manager, then re-run this script.{C_END}")
                sys.exit(1)
            print(f"\n{C_CYAN}{EMOJI_INFO} Tor installation step finished.{C_END}\n")
        else:
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Could not detect a supported package manager (apt, yum, pacman).{C_END}")
            print(f"{C_WARNING}{EMOJI_INFO} Please install Tor manually for your Linux distribution and re-run the script.{C_END}")
            sys.exit(1)
    else:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor is already installed!{C_END}\n")

def is_tor_service_running():
    try:
        result = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0 and result.stdout.strip():
            return True
        if is_command_available("systemctl"):
            result_systemctl = subprocess.run(["systemctl", "is-active", "--quiet", "tor"])
            if result_systemctl.returncode == 0:
                return True
        return False
    except Exception:
        return False

def ensure_tor_service_running():
    print(f"\n{C_BLUE}{EMOJI_TOR} Checking Tor service status...{C_END}")
    if not is_tor_service_running():
        print(f"\n{C_WARNING}{EMOJI_WARNING} Tor service is not running. Starting Tor service (requires sudo privileges)...{C_END}")
        started = False
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner_animation, args=(f"Starting Tor service...", stop_event), kwargs={"emoji": EMOJI_TOR, "color": C_CYAN})
        spinner_thread.start()
        try:
            if is_command_available("systemctl"):
                proc = subprocess.run(["sudo", "systemctl", "start", "tor.service"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(2)
                if is_tor_service_running():
                    started = True
            if not started and is_command_available("service"):
                proc = subprocess.run(["sudo", "service", "tor", "start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(2)
                if is_tor_service_running():
                    started = True
            stop_event.set()
            spinner_thread.join()
            if started:
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor service started successfully!{C_END}\n")
            else:
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to start Tor service!{C_END}")
                print(f"{C_WARNING}{EMOJI_INFO} Please start Tor manually using 'sudo systemctl start tor.service' or 'sudo service tor start', then re-run this script.{C_END}")
                sys.exit(1)
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Exception during Tor service start: {e}{C_END}")
            print(f"{C_WARNING}{EMOJI_INFO} Please start Tor manually using 'sudo systemctl start tor.service' or 'sudo service tor start', then re-run this script.{C_END}")
            sys.exit(1)
        print(f"\n{C_CYAN}{EMOJI_INFO} Tor service start step finished.{C_END}\n")
    else:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor service is already running!{C_END}\n")

# --- EXECUTE PRIORITIZED SETUP CHECKS ---
require_venv_or_exit() # Step 1: Must be in VENV
check_and_install_python_dependencies() # Step 2: Install Python packages (inside venv)
ensure_tor_installed() # Step 3: Install Tor (system-wide)
ensure_tor_service_running() # Step 4: Start Tor service

# --- SHOW ANIMATED BANNER ---
print_animated_banner()

print(f"{C_GREEN}{EMOJI_ROCKET}{C_BOLD}{EMOJI_CELEBRATE} All system checks passed! KADDU YT-VIEWS is ready to launch!{C_END}\n")
# --- PRIORITIZED SETUP ENDS HERE ---
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
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'

EMOJIS = {
    'video': '🎬',
    'short': '🎞️',
    'info': 'ℹ️',
    'success': '✅',
    'error': '❌',
    'wait': '⏳',
    'prompt': '👉',
    'star': '⭐',
    'rocket': '🚀',
    'link': '🔗',
    'spinner': '🔄',
    'check': '✔️',
    'cross': '✖️',
    'thread': '🧵',
    'progress': '📊',
    'tip': '💡',
    'next': '➡️',
    'pause': '⏸️',
    'dryrun': '📝',
    'kaddu': '🎃', 
    'views': '👀', 
}

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
    spinner_chars = ['|', '/', '-', '\\']
    end_time = time.time() + seconds
    idx = 0
    while time.time() < end_time:
        print(f"\r{Colors.WARNING}{EMOJIS['wait']} {message} {spinner_chars[idx % 4]}{Colors.ENDC}", end='', flush=True)
        time.sleep(0.2)
        idx += 1
    print("\r" + " " * (len(message) + 5) + "\r", end='') # Clear line

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
        # print(f"{Colors.WARNING}{EMOJIS['error']} Link validation error for {link} on port {tor_port}: {e}{Colors.ENDC}") # Debug
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
        # print(f"{Colors.WARNING}{EMOJIS['error']} View simulation error for {link} on port {tor_port}: {e}{Colors.ENDC}") # Debug
        return False

# Install requirements and Tor (replaces old install_requirements)
def install_requirements_and_tor():
    """
    Installs required Python packages from requirements.txt and ensures Tor is installed and running.
    Prioritizes 'apt' and 'service' for Tor installation/start on compatible Linux systems,
    then falls back to pytor's internal methods.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['star']} System Setup {EMOJIS['star']}{Colors.ENDC}")
    
    # 1. Install Python Packages
    try:
        requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        if not os.path.exists(requirements_file):
            print(f"{Colors.FAIL}{EMOJIS['error']} [CRITICAL] requirements.txt not found!{Colors.ENDC}")
            print(f"{Colors.WARNING}{EMOJIS['info']} Creating a basic '{requirements_file}' with essential packages: requests, PySocks.{Colors.ENDC}")
            # Ensure the user is aware of what's being written.
            with open(requirements_file, 'w') as f:
                f.write("requests\n")
                f.write("PySocks\n")
            print(f"{Colors.OKGREEN}{EMOJIS['success']} Basic requirements.txt created. Please review its contents if you have other dependencies.{Colors.ENDC}")

        print(f"\n{Colors.OKBLUE}{EMOJIS['wait']} Installing/Updating Python packages from '{requirements_file}'... This might take a moment.{Colors.ENDC}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print(f"{Colors.OKGREEN}{EMOJIS['success']} Python packages installed/updated successfully.{Colors.ENDC}")

    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] Failed to install Python packages: {e}{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] An unexpected error occurred during package installation: {e}{Colors.ENDC}")
        sys.exit(1)

    # 2. Tor Setup
    print(f"\n{Colors.OKBLUE}{EMOJIS['wait']} Checking and ensuring Tor service...{Colors.ENDC}")
    tor_setup_successful = False

    # --- User-requested direct method: apt and service ---
    preferred_method_attempted = False
    if os.name == 'posix' and shutil.which('apt') and shutil.which('service'):
        preferred_method_attempted = True
        print(f"{Colors.OKCYAN}{EMOJIS['info']} Attempting preferred Tor setup: 'sudo apt update/install tor' & 'sudo service tor start'.{Colors.ENDC}")
        try:
            # Update package lists
            print(f"{Colors.GRAY}  Updating package lists (sudo apt update -y)...{Colors.ENDC}")
            subprocess.check_call(['sudo', 'apt', 'update', '-y'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"{Colors.OKGREEN}{EMOJIS['success']} Package lists updated.{Colors.ENDC}")

            # Install Tor
            print(f"{Colors.GRAY}  Installing Tor (sudo apt install tor -y)...{Colors.ENDC}")
            subprocess.check_call(['sudo', 'apt', 'install', 'tor', '-y'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"{Colors.OKGREEN}{EMOJIS['success']} Tor installed/verified via apt.{Colors.ENDC}")

            # Start Tor service
            print(f"{Colors.GRAY}  Starting Tor service (sudo service tor start)...{Colors.ENDC}")
            subprocess.check_call(['sudo', 'service', 'tor', 'start'], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            # Add a small delay for the service to actually start
            spinner(5, "Waiting for Tor service to initialize after 'sudo service tor start' command")
            print(f"{Colors.OKGREEN}{EMOJIS['success']} 'sudo service tor start' command issued.{Colors.ENDC}")
            
            # Quick verification if Tor process is running
            # This is a basic check; full functionality is tested by get_ip later
            try:
                pgrep_check = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if pgrep_check.returncode == 0 and pgrep_check.stdout.strip():
                    print(f"{Colors.OKGREEN}{EMOJIS['check']} Tor process detected running after service start.{Colors.ENDC}")
                    tor_setup_successful = True
                else:
                    print(f"{Colors.WARNING}{EMOJIS['error']} Tor process not detected after 'service tor start'. It might take longer or have failed silently.{Colors.ENDC}")
                    # We'll still mark as potentially successful because the service command itself didn't error.
                    # The IP check later in the script will be the definitive test.
                    tor_setup_successful = True # Assuming service start was okay if no error from subprocess
            except FileNotFoundError:
                print(f"{Colors.WARNING} pgrep not found, cannot verify Tor process directly after service start. Assuming success if 'service tor start' did not error.{Colors.ENDC}")
                tor_setup_successful = True # Assuming okay

        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] Preferred Tor setup ('apt'/'service') failed: {e}{Colors.ENDC}")
            print(f"{Colors.FAIL}   Stderr: {e.stderr.decode(errors='ignore').strip() if e.stderr else 'N/A'}{Colors.ENDC}")
            if e.returncode == 100 and "Unable to lock an administration directory" in e.stderr.decode(errors='ignore'):
                print(f"{Colors.WARNING}{EMOJIS['info']} This might be due to another package manager running. Please ensure no other apt/dpkg processes are active.{Colors.ENDC}")

        except FileNotFoundError as e:
            print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] A command was not found during preferred Tor setup (e.g., sudo, apt, service): {e}{Colors.ENDC}")
    
    # --- Fallback to pytor's internal setup if preferred method wasn't applicable, or failed, or didn't set tor_setup_successful ---
    if not tor_setup_successful:
        if preferred_method_attempted:
            print(f"\n{Colors.OKBLUE}{EMOJIS['info']} Preferred 'apt/service' Tor setup failed or did not confirm success. Trying fallback 'pytor' methods...{Colors.ENDC}")
        else:
            print(f"\n{Colors.OKBLUE}{EMOJIS['info']} Preferred 'apt/service' Tor setup not applicable for this system. Trying 'pytor' internal Tor setup...{Colors.ENDC}")
        
        try:
            pytor.check_dependencies() # Checks for tor/curl on Linux and tries to install them if missing using package managers.
            pytor.start_tor()        # Starts Tor service using methods in pytor.py
            print(f"{Colors.OKGREEN}{EMOJIS['success']} 'pytor' internal Tor setup/start attempt completed.{Colors.ENDC}")
            # We assume pytor.start_tor() is successful if it doesn't raise an exception.
            # The true test will be the IP check later.
            tor_setup_successful = True 
        except Exception as e:
            print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] Fallback 'pytor' internal Tor setup failed: {e}{Colors.ENDC}")

    # 3. Final Check
    if not tor_setup_successful:
        print(f"\n{Colors.FAIL}{EMOJIS['error']} [CRITICAL ERROR] All attempts to set up and start Tor failed.{Colors.ENDC}")
        print(f"{Colors.WARNING}Please ensure Tor can be installed and started on your system, or that it's already running and accessible.{Colors.ENDC}")
        print(f"{Colors.WARNING}  - On Linux, verify 'sudo apt install tor' and 'sudo service tor start' work manually.{Colors.ENDC}")
        print(f"{Colors.WARNING}  - Or, check Tor logs for issues (e.g., /var/log/tor/log or similar).{Colors.ENDC}")
        sys.exit(1)
    else:
        print(f"\n{Colors.OKGREEN}{EMOJIS['success']} Tor setup phase completed. IP connectivity will be tested next.{Colors.ENDC}")

def get_user_links():
    """
    Prompts the user for link details (URL, type, length) with an improved workflow.
    First asks for the type of content (videos, shorts, or mixed).
    Then, for each batch of a specific type, it can ask for a default length.
    Returns a list of link dictionaries.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['link']} Let's add your content! {EMOJIS['link']}{Colors.ENDC}")
    links = []
    link_id_counter = 0

    while True:
        print(f"{Colors.OKCYAN}What kind of content do you want to add?{Colors.ENDC}")
        print(f"  1. Only YouTube Videos {EMOJIS['video']}")
        print(f"  2. Only YouTube Shorts {EMOJIS['short']}")
        print(f"  3. Both Videos and Shorts (Mixed)")
        content_choice_str = input(f"{Colors.OKCYAN}{EMOJIS['prompt']} Enter your choice (1-3) [Press Enter for 1]: {Colors.ENDC}").strip()
        if content_choice_str.lower() == 'help':
            print(HELP_TEXT)
            continue
        
        content_choice = '1' # Default to Videos
        if content_choice_str in ['1', '2', '3']:
            content_choice = content_choice_str
        elif not content_choice_str: # Enter for default
            pass # Keeps default '1'
        else:
            print(f"{Colors.WARNING}{EMOJIS['error']} Invalid choice. Please enter 1, 2, or 3.{Colors.ENDC}")
            continue
        break

    content_types_to_add = []
    if content_choice == '1':
        content_types_to_add.append(('video', EMOJIS['video']))
    elif content_choice == '2':
        content_types_to_add.append(('short', EMOJIS['short']))
    elif content_choice == '3':
        content_types_to_add.append(('video', EMOJIS['video']))
        content_types_to_add.append(('short', EMOJIS['short']))

    for content_type, content_emoji in content_types_to_add:
        print(f"\n{Colors.HEADER}--- Adding {content_type.capitalize()}s {content_emoji} ---{Colors.ENDC}")
        
        while True:
            try:
                num_items_str = input(f"{Colors.OKCYAN}{EMOJIS['prompt']} How many {content_type}s? (Enter a number, 0 to skip): {Colors.ENDC}").strip()
                if num_items_str.lower() == 'help':
                    print(HELP_TEXT)
                    continue
                num_items = int(num_items_str) if num_items_str else 0
                if num_items < 0:
                    print(f"{Colors.WARNING}{EMOJIS['error']} Please enter a non-negative number.{Colors.ENDC}")
                    continue
                if num_items == 0:
                    print(f"{Colors.OKBLUE}Skipping {content_type}s.{Colors.ENDC}")
                    break 
                break
            except ValueError:
                print(f"{Colors.WARNING}{EMOJIS['error']} Invalid input. Please enter a number.{Colors.ENDC}")
        if num_items == 0: continue

        # Ask for a default length for this batch of content_type
        default_length_for_batch = None
        min_length = 10 if content_type == 'short' else 60
        suggested_length = 60 if content_type == 'short' else 300

        while True:
            use_default_len_str = input(f"  {EMOJIS['prompt']} Set a default length for these {num_items} {content_type}s? (yes/no) [Enter for no]: {Colors.ENDC}").strip().lower()
            if use_default_len_str == 'help': print(HELP_TEXT); continue
            if use_default_len_str in ['y', 'yes']:
                while True:
                    length_str = input(f"    {EMOJIS['prompt']} Enter default length for {content_type}s in seconds [Enter for {suggested_length}s]: {Colors.ENDC}").strip()
                    if length_str.lower() == 'help': print(HELP_TEXT); continue
                    try:
                        default_length_for_batch = int(length_str) if length_str else suggested_length
                        if default_length_for_batch < min_length:
                            print(f"{Colors.WARNING}{EMOJIS['error']} Min length for {content_type} is {min_length}s.{Colors.ENDC}")
                            default_length_for_batch = None # Reset
                            continue
                        break
                    except ValueError:
                        print(f"{Colors.WARNING}{EMOJIS['error']} Invalid number for length.{Colors.ENDC}")
                break
            elif use_default_len_str in ['n', 'no', '']:
                break
            else:
                print(f"{Colors.WARNING}{EMOJIS['error']} Invalid choice. Please enter 'yes' or 'no'.{Colors.ENDC}")

        for i in range(num_items):
            print(f"\n{Colors.OKBLUE}--- {content_type.capitalize()} #{i+1} ---{Colors.ENDC}")
            while True:
                link_url = input(f"  {EMOJIS['prompt']} Enter URL for {content_type} #{i+1}: ").strip()
                if link_url.lower() == 'help': print(HELP_TEXT); continue
                if not link_url: print(f"{Colors.WARNING}{EMOJIS['error']} URL cannot be empty.{Colors.ENDC}"); continue
                if not (link_url.startswith("http://") or link_url.startswith("https://")):
                    print(f"{Colors.WARNING}{EMOJIS['error']} Invalid URL. Must start with http:// or https://{Colors.ENDC}"); continue
                break
            
            current_length_sec = default_length_for_batch
            if current_length_sec is None: # If no batch default, ask individually
                length_prompt = f"  {EMOJIS['prompt']} Enter {content_type} length in seconds [Enter for {suggested_length}s]: "
                while True:
                    length_str = input(length_prompt).strip()
                    if length_str.lower() == 'help': print(HELP_TEXT); continue
                    try:
                        current_length_sec = int(length_str) if length_str else suggested_length
                        if current_length_sec < min_length:
                            print(f"{Colors.WARNING}{EMOJIS['error']} Min length for {content_type} is {min_length}s.{Colors.ENDC}"); continue
                        break
                    except ValueError:
                        print(f"{Colors.WARNING}{EMOJIS['error']} Invalid input. Please enter a number for length.{Colors.ENDC}")
            
            links.append({'url': link_url, 'type': content_type, 'length': current_length_sec, 'id': link_id_counter})
            link_id_counter += 1
            
    if not links:
        print(f"{Colors.WARNING}{EMOJIS['info']} No content was added.{Colors.ENDC}")
    return links

def get_views_per_link():
    """
    Prompts user for number of views per link.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['views']} View Configuration {EMOJIS['views']}{Colors.ENDC}")
    while True:
        views_str = input(f"{Colors.OKCYAN}{EMOJIS['prompt']} How many views per link? (e.g., 100) [Press Enter for 10, 0 for 'continuous']: {Colors.ENDC}").strip()
        if views_str.lower() == 'help':
            print(HELP_TEXT)
            continue
        try:
            views = int(views_str) if views_str else 10
            if views < 0:
                print(f"{Colors.WARNING}{EMOJIS['error']} Please enter 0 or a positive number.{Colors.ENDC}")
                continue
            return views 
        except ValueError:
            print(f"{Colors.WARNING}{EMOJIS['error']} Invalid input. Please enter a number.{Colors.ENDC}")

def get_connection_count():
    """
    Prompts user for number of parallel Tor connections.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['thread']} Connection Setup {EMOJIS['thread']}{Colors.ENDC}")
    print(f"   (More connections can mean faster view generation but need Tor to be set up for multiple SOCKS ports if > 1)")
    while True:
        num_connections_str = input(f"{Colors.OKCYAN}{EMOJIS['prompt']} How many parallel connections (Tor circuits)? (1-10) [Press Enter for 1]: {Colors.ENDC}").strip()
        if num_connections_str.lower() == 'help':
            print(HELP_TEXT)
            print(f"{Colors.OKBLUE}{EMOJIS['info']} Each connection uses a distinct Tor SOCKS port (e.g., 9050, 9051...). Ensure Tor is configured if using >1.{Colors.ENDC}")
            continue
        try:
            num_connections = int(num_connections_str) if num_connections_str else 1
            if not 1 <= num_connections <= 10:
                print(f"{Colors.WARNING}{EMOJIS['error']} Please enter a number between 1 and 10.{Colors.ENDC}")
                continue
            return num_connections
        except ValueError:
            print(f"{Colors.WARNING}{EMOJIS['error']} Invalid input. Please enter a number.{Colors.ENDC}")

def get_dry_run_choice():
    """
    Asks if user wants a dry run.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['dryrun']} Dry Run Option {EMOJIS['dryrun']}{Colors.ENDC}")
    while True:
        choice = input(f"{Colors.OKCYAN}{EMOJIS['prompt']} Perform a 'dry run' first? (yes/no) [Press Enter for no]: {Colors.ENDC}").strip().lower()
        if choice == 'help':
            print(HELP_TEXT)
            print(f"{Colors.OKBLUE}{EMOJIS['info']} Dry run simulates without actual views.{Colors.ENDC}")
            continue
        if choice in ['yes', 'y']:
            return True
        if choice in ['no', 'n', '']:
            return False
        print(f"{Colors.WARNING}{EMOJIS['error']} Invalid choice. Please enter 'yes' or 'no'.{Colors.ENDC}")

# Check if running as root/admin
def check_root():
    # On Linux/Unix systems
    if os.name == 'posix':
        if os.geteuid() != 0:
            print("\033[1;31mERROR:\033[0m This script must be run as root.")
            print("Please run with: sudo python3 main.py")
            sys.exit(1)
    # Removed Windows admin check as script is now Linux-only
    # elif os.name == 'nt':
    #     import ctypes
    #     if not ctypes.windll.shell32.IsUserAnAdmin():
    #         print("\033[1;31mERROR:\033[0m This script must be run as administrator.")
    #         print("Please right-click on Command Prompt or PowerShell and select 'Run as administrator'")
    #         sys.exit(1)

def validate_all_links(links, tor_ports):
    """
    Validates all user-provided links using available Tor ports in a round-robin fashion.
    Args:
        links (list): List of link dictionaries.
        tor_ports (list): List of available Tor SOCKS port numbers.
    Returns:
        list: A list of valid link dictionaries. Invalid links are reported and excluded.
    """
    print(f"\n{Colors.OKBLUE}{EMOJIS['check']} Validating links...{Colors.ENDC}")
    valid_links = []
    if not tor_ports:
        print(f"{Colors.FAIL}{EMOJIS['error']} No Tor ports available for link validation. Check Tor setup.{Colors.ENDC}")
        return []

    for i, link_info in enumerate(links):
        # Cycle through tor_ports for validation to distribute load and mimic multiple connections
        port_to_use = tor_ports[i % len(tor_ports)] 
        is_valid = validate_link(link_info['url'], port_to_use)
        if is_valid:
            print(f"{Colors.OKGREEN}{EMOJIS['success']} Link #{link_info['id']+1} ({link_info['url'][:60]}...) is valid via port {port_to_use}.{Colors.ENDC}")
            valid_links.append(link_info)
        else:
            print(f"{Colors.FAIL}{EMOJIS['error']} Link #{link_info['id']+1} ({link_info['url'][:60]}...) is invalid or unreachable via Tor port {port_to_use}. It will be skipped.{Colors.ENDC}")
    
    if not valid_links:
        print(f"{Colors.WARNING}{EMOJIS['cross']} No valid links to process after validation.{Colors.ENDC}")
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

def show_tor_status(base_tor_port, num_connections):
    """
    Attempts to get and display the current IP for each configured Tor SOCKS port.
    Args:
        base_tor_port (int): The starting SOCKS port for Tor.
        num_connections (int): Number of Tor connections/ports to check.
    """
    print(f"\n{Colors.OKBLUE}{EMOJIS['info']} Checking Tor Connection Status & IPs for {num_connections} configured circuit(s)...{Colors.ENDC}")
    any_successful = False
    all_ports_checked = []

    if num_connections == 0: # Should ideally not happen if logic is correct elsewhere
        print(f"{Colors.WARNING}{EMOJIS['error']} No connections configured to check Tor status.{Colors.ENDC}")
        return

    for i in range(num_connections):
        port = base_tor_port + i
        all_ports_checked.append(str(port))
        print(f"{Colors.GRAY}  {EMOJIS['wait']} Attempting to get IP for Tor SOCKS port {Colors.BOLD}{port}{Colors.ENDC}{Colors.GRAY}...{Colors.ENDC}")
        try:
            # pytor.get_ip is verbose and will print its own success/failure for the IP itself.
            # It exits on total failure for that port, so we might not always see the messages below if it exits.
            current_ip = pytor.get_ip(tor_port=port) 
            if current_ip: # Should always be true if pytor.get_ip didn't exit
                # The detailed IP and service used is printed by pytor.get_ip
                # Here we just confirm this port in main.py context was successful.
                print(f"{Colors.OKGREEN}  {EMOJIS['success']} Successfully connected via SOCKS Port {Colors.BOLD}{port}{Colors.ENDC}{Colors.OKGREEN}. External IP confirmed.{Colors.ENDC}")
                any_successful = True
            # else: # This path is less likely if pytor.get_ip exits on failure.
                # print(f"{Colors.FAIL}  {EMOJIS['error']} Could not get IP for Port {port} (as reported by pytor.get_ip).{Colors.ENDC}")
        except SystemExit:
            # This handles the case where pytor.get_ip calls sys.exit(1) after all its retries fail for a port.
            print(f"{Colors.FAIL}  {EMOJIS['error']} Failed to get an IP for Tor SOCKS Port {Colors.BOLD}{port}{Colors.ENDC}{Colors.FAIL} after multiple attempts. Check Tor logs for issues with this port.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}  {EMOJIS['error']} An unexpected error occurred while checking Tor Port {Colors.BOLD}{port}{Colors.ENDC}{Colors.FAIL}: {e}{Colors.ENDC}")
    
    if any_successful:
        print(f"{Colors.OKGREEN}{EMOJIS['success']} Tor IP checks completed. At least one connection is working.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{EMOJIS['error']} CRITICAL: Failed to confirm external IP for ANY configured Tor SOCKS port(s): {', '.join(all_ports_checked)}.{Colors.ENDC}")
        print(f"{Colors.WARNING}  Please check your Tor installation, configuration (torrc for multiple SOCKS ports if using >1), and ensure the Tor service is running and accessible.{Colors.ENDC}")
        print(f"{Colors.WARNING}  View generation cannot proceed without at least one working Tor connection.{Colors.ENDC}")
        # Potentially sys.exit(1) here if this is deemed absolutely critical before link validation

def dry_run_summary(links, views_per_link, num_connections, base_tor_port):
    """
    Displays a summary of what the script would do in a dry run.
    Args:
        links (list): List of (validated) link dictionaries.
        views_per_link (int): Number of views planned per link (0 for continuous).
        num_connections (int): Number of parallel connections planned.
        base_tor_port (int): Base Tor SOCKS port for reference.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['dryrun']} DRY RUN SUMMARY {EMOJIS['dryrun']}{Colors.ENDC}")
    if not links:
        print(f"{Colors.WARNING}No (valid) links to process for dry run.{Colors.ENDC}")
        return

    print(f"{Colors.OKBLUE}Dry Run Configuration:{Colors.ENDC}")
    print(f"  - Target views per link: {Colors.BOLD}{views_per_link if views_per_link > 0 else 'Continuous (until stopped)'}{Colors.ENDC}")
    print(f"  - Parallel connections (threads): {Colors.BOLD}{num_connections}{Colors.ENDC}")
    tor_ports_display = [str(base_tor_port + i) for i in range(num_connections)]
    print(f"  - Tor SOCKS ports to be used: {Colors.BOLD}{', '.join(tor_ports_display)}{Colors.ENDC}")
    
    print(f"\n{Colors.OKBLUE}Target Links To Be Processed ({len(links)}):{Colors.ENDC}")
    for idx, link_info in enumerate(links):
        print(f"  {idx+1}. {EMOJIS['link']} {link_info['url']} ({link_info['type']}, {link_info['length']}s watch time per view)")

    estimated_time = estimate_total_time(links, views_per_link, num_connections)
    print(f"\n{Colors.OKBLUE}Estimated total processing time (very approximate): {Colors.BOLD}{estimated_time}{Colors.ENDC}")
    print(f"{Colors.WARNING}This was a dry run. No actual web requests would be made to target URLs, and no views would be generated.{Colors.ENDC}")
    print(TIP_TEXT)

# --- Globals for View Worker Threads ---
completed_views_lock = threading.Lock()
completed_views_total = 0 # Tracks total views across all links in the current run
views_per_link_tracker = {} # Tracks views for each specific link_id in the current run
stop_event_global = threading.Event() # Used to signal all worker threads to stop

def check_virtual_environment():
    """
    Checks if the script is running inside a Python virtual environment.
    If not, prints a warning and guidance to the user.
    """
    if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        print(f"\n{Colors.WARNING}{EMOJIS['error']} WARNING: You are not running this script in a Python virtual environment.{Colors.ENDC}")
        print(f"{Colors.GRAY}Running without a virtual environment can lead to dependency conflicts and unexpected errors (like 'Missing dependencies for SOCKS support').{Colors.ENDC}")
        print(f"{Colors.OKBLUE}It is STRONGLY recommended to use a virtual environment.{Colors.ENDC}")
        print(f"{Colors.OKGREEN}To create and use a virtual environment (on most systems):{Colors.ENDC}")
        print(f"{Colors.BOLD}  1. python3 -m venv .venv{Colors.ENDC}  (Creates a venv folder named '.venv')")
        print(f"{Colors.BOLD}  2. source .venv/bin/activate{Colors.ENDC} (On Linux/macOS)")
        print(f"{Colors.BOLD}     OR{Colors.ENDC}")
        print(f"{Colors.BOLD}     .venv\\Scripts\\activate{Colors.ENDC} (On Windows CMD/PowerShell)")
        print(f"{Colors.BOLD}  3. pip install -r requirements.txt{Colors.ENDC} (Install dependencies INSIDE the venv)")
        print(f"{Colors.BOLD}  4. python3 main.py{Colors.ENDC} (Run the script from within the activated venv)")
        print(f"{Colors.GRAY}You may need to press Enter to continue if the script proceeds...{Colors.ENDC}")
        input(f"{Colors.WARNING}Press Enter to acknowledge and continue without a venv (NOT RECOMMENDED), or Ctrl+C to exit and set up a venv: {Colors.ENDC}")
    else:
        print(f"{Colors.OKGREEN}{EMOJIS['success']} Running inside a Python virtual environment. Good job!{Colors.ENDC}")

def view_worker(link_info, views_to_generate_for_this_link, tor_ports_available, progress_callback_func):
    """
    Worker function executed by each thread to simulate views for a single link.
    It handles IP rotation (by picking from available tor_ports_available) and view timing.
    Args:
        link_info (dict): Dictionary containing {'url', 'type', 'length', 'id'} for the link.
        views_to_generate_for_this_link (int): Number of views to generate for this specific link (0 for continuous).
        tor_ports_available (list): List of available Tor SOCKS port numbers for this worker to use.
        progress_callback_func (function): Callback function to report progress.
                                        Expected signature: callback(link_id, views_done_for_link, total_overall_views, url, success_flag, port_used, watch_duration)
    """
    global completed_views_total, views_per_link_tracker, stop_event_global

    link_id = link_info['id']
    link_url = link_info['url']
    is_short_video = link_info['type'] == 'short'
    base_video_length = link_info['length']
    
    local_views_done_count = 0 # Views done by this worker for this specific link

    if not tor_ports_available:
        print(f"{Colors.FAIL}{EMOJIS['error']} Critical: No Tor ports assigned to worker for {link_url}. Worker exiting.{Colors.ENDC}")
        return # Cannot proceed without Tor ports

    # Each worker can start at a random port to distribute initial load slightly
    current_port_index = random.randrange(len(tor_ports_available))

    # Loop for generating views until the target is met or stop_event is set
    while not stop_event_global.is_set():
        if views_to_generate_for_this_link > 0 and local_views_done_count >= views_to_generate_for_this_link:
            # print(f"{Colors.OKGREEN}Worker for link ID {link_id} completed its {local_views_done_count} views.{Colors.ENDC}")
            break # Target views for this link reached

        # Select Tor port for this attempt (round-robin from available ports)
        chosen_tor_port = tor_ports_available[current_port_index % len(tor_ports_available)]
        current_port_index += 1 # Move to next port for next iteration

        # Simulate delay before starting the view (human-like behavior)
        pre_view_delay = get_random_start_delay()
        # print(f"{Colors.GRAY}Worker (LID:{link_id}, Port:{chosen_tor_port}): Delaying {pre_view_delay}s for {link_url[:30]}...{Colors.ENDC}")
        # Sleep in small chunks to check stop_event frequently
        sleep_chunk_end_time = time.time() + pre_view_delay
        while time.time() < sleep_chunk_end_time:
            if stop_event_global.is_set(): break
            time.sleep(min(0.5, sleep_chunk_end_time - time.time()))
        if stop_event_global.is_set(): break

        # Determine actual watch time for this view
        actual_watch_time = get_random_watch_time(base_video_length, is_short_video)
        
        # print(f"{Colors.GRAY}Worker (LID:{link_id}, Port:{chosen_tor_port}): Attempting view on {link_url[:30]}... (watch {actual_watch_time}s).{Colors.ENDC}")
        
        if stop_event_global.is_set(): break # Check just before the blocking network call
        view_successful = simulate_view(link_url, chosen_tor_port, actual_watch_time)
        if stop_event_global.is_set(): break # Check immediately after the network call returns
        
        if view_successful:
            with completed_views_lock: # Thread-safe update of shared counters
                completed_views_total += 1
                local_views_done_count += 1
                # Update tracker for this specific link
                views_per_link_tracker[link_id] = views_per_link_tracker.get(link_id, 0) + 1
                current_link_total_views = views_per_link_tracker[link_id]
            # Report progress: link_id, views_done_for_this_link_by_this_worker, total_overall_views, url, success_flag, port, watch_time
            progress_callback_func(link_id, current_link_total_views, completed_views_total, link_url, True, chosen_tor_port, actual_watch_time)
        else:
            with completed_views_lock: # Access tracker safely even on failure if needed for accurate count before failure
                 current_link_total_views = views_per_link_tracker.get(link_id, 0)
            progress_callback_func(link_id, current_link_total_views, completed_views_total, link_url, False, chosen_tor_port, actual_watch_time)

        # Delay between consecutive views by this worker (human-like behavior)
        # Longer delay if in continuous mode (views_to_generate_for_this_link == 0)
        post_view_delay_base = 10 if views_to_generate_for_this_link == 0 else 5
        post_view_delay = random.uniform(post_view_delay_base, post_view_delay_base + 10)
        # print(f"{Colors.GRAY}Worker (LID:{link_id}, Port:{chosen_tor_port}): Post-view delay {post_view_delay:.1f}s for {link_url[:30]}...{Colors.ENDC}")
        
        sleep_chunk_end_time = time.time() + post_view_delay
        while time.time() < sleep_chunk_end_time:
            if stop_event_global.is_set(): break
            time.sleep(min(0.5, sleep_chunk_end_time - time.time())) # Check for stop signal frequently
        if stop_event_global.is_set(): break
            
    # if stop_event_global.is_set():
    #     print(f"{Colors.YELLOW}Worker for link ID {link_id} ({link_url[:30]}...) received stop signal and is terminating. Views by this worker: {local_views_done_count}.{Colors.ENDC}")
    # else:
    #     print(f"{Colors.OKBLUE}Worker for link ID {link_id} ({link_url[:30]}...) finished its tasks. Views by this worker: {local_views_done_count}.{Colors.ENDC}")

def main():
    """Main function to run the YouTube view generation system."""
    # os.system('') # Removed for Linux-only
    print_animated_banner()
    
    check_virtual_environment()
    check_root()
    install_requirements_and_tor()

    print(TIP_TEXT)
    if input(f"{Colors.OKCYAN}{EMOJIS['prompt']} Press Enter to continue or type 'help': {Colors.ENDC}").strip().lower() == 'help':
        print(HELP_TEXT)

    user_links_data = get_user_links()
    if not user_links_data:
        print(f"{Colors.FAIL}{EMOJIS['error']} No links provided. Exiting.{Colors.ENDC}")
        sys.exit(1)

    views_per_target_link = get_views_per_link()
    num_parallel_connections = get_connection_count()
    
    base_tor_socks_port = 9050 
    tor_ports_to_use = [base_tor_socks_port + i for i in range(num_parallel_connections)]

    show_tor_status(base_tor_socks_port, num_parallel_connections)
    validated_links = validate_all_links(user_links_data, tor_ports_to_use)
    
    if not validated_links: 
        print(f"{Colors.FAIL}{EMOJIS['error']} No valid links to process after validation. Exiting.{Colors.ENDC}")
        sys.exit(1)

    is_dry_run = get_dry_run_choice()
    if is_dry_run:
        dry_run_summary(validated_links, views_per_target_link, num_parallel_connections, base_tor_socks_port)
        print(f"\n{Colors.OKGREEN}Dry run complete. Exiting.{Colors.ENDC}")
        sys.exit(0)

    print(f"\n{Colors.HEADER}{EMOJIS['rocket']} STARTING VIEW GENERATION {EMOJIS['rocket']}{Colors.ENDC}")
    estimated_time_str = estimate_total_time(validated_links, views_per_target_link, num_parallel_connections)
    print(f"{Colors.OKBLUE}Estimated total time: {Colors.BOLD}{estimated_time_str}{Colors.ENDC}")
    if views_per_target_link == 0:
        print(f"{Colors.WARNING}Running in continuous mode. Press Ctrl+C to stop.{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}This is a rough estimate. Actual time may vary.{Colors.ENDC}")
    
    if input(f"{Colors.OKCYAN}{EMOJIS['prompt']} Press Enter to start, or type 'quit' to exit: {Colors.ENDC}").strip().lower() == 'quit':
        print(f"{Colors.OKBLUE}Exiting as requested.{Colors.ENDC}")
        sys.exit(0)

    global completed_views_total, views_per_link_tracker, stop_event_global
    completed_views_total = 0
    views_per_link_tracker = {link['id']: 0 for link in validated_links}
    stop_event_global.clear() # Crucial: Clear event at the start of a new run

    start_time_proc = time.time()

    def progress_update_handler(link_id, views_done_link, total_done_overall, url, success, port, watch_time):
        status_emoji = EMOJIS['success'] if success else EMOJIS['error']
        status_color = Colors.OKGREEN if success else Colors.WARNING
        action_color = Colors.OKGREEN if success else Colors.FAIL
        short_url = url[:40] + '...' if len(url) > 43 else url
        action_taken = "Viewed" if success else "View Failed"
        # Improved: Add more spacing and clear formatting
        progress_line = f"\r{status_color}{status_emoji}{Colors.ENDC} {Colors.BOLD}Link #{link_id}{Colors.ENDC} ({Colors.GRAY}{short_url}{Colors.ENDC}) - {action_color}{action_taken}{Colors.ENDC} ({Colors.OKBLUE}Port:{port}, Watched:{watch_time}s{Colors.ENDC}). This link: {Colors.BOLD}{views_done_link}{Colors.ENDC}. Total: {Colors.BOLD}{total_done_overall}{Colors.ENDC}    "
        print(progress_line, end='', flush=True)
        # Print a summary less frequently to avoid too much scroll
        if num_parallel_connections == 0 : num_parallel_connections = 1
        print_summary_interval = max(1, (num_parallel_connections * 2) + (num_parallel_connections // 2))
        if not validated_links: print_summary_interval = 1
        if total_done_overall % print_summary_interval == 0 or total_done_overall == 1:
            elapsed_time = time.time() - start_time_proc
            elapsed_time_str = f"{elapsed_time // 60:.0f}m {elapsed_time % 60:.0f}s" if elapsed_time >=60 else f"{elapsed_time:.1f}s"
            avg_time_per_view = elapsed_time / total_done_overall if total_done_overall > 0 else 0
            # Ensure a newline before this summary, as the progress_line uses \r
            print("\n") # Extra newline for spacing
            print(f"{Colors.HEADER}{EMOJIS['kaddu']} {'-'*20} KADDU YT-VIEWS: PROGRESS {'-'*20} {EMOJIS['kaddu']}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}  {EMOJIS['progress']} {Colors.BOLD}Overall Status @ {time.strftime('%H:%M:%S')}{Colors.ENDC}")
            print(f"{Colors.GRAY}  -----------------------------------------------------------{Colors.ENDC}")
            print(f"{Colors.OKBLUE}  {EMOJIS['thread']} Active Parallel Connections: {Colors.BOLD}{num_parallel_connections}{Colors.ENDC}")
            print(f"{Colors.OKGREEN}  {EMOJIS['success']} Total Views Generated So Far: {Colors.BOLD}{total_done_overall}{Colors.ENDC}")
            if views_per_target_link > 0:
                total_target_views = len(validated_links) * views_per_target_link
                views_remaining = total_target_views - total_done_overall
                completion_percent = (total_done_overall / total_target_views) * 100 if total_target_views > 0 else 0
                print(f"{Colors.WARNING}  {EMOJIS['wait']} Target Views Remaining: {Colors.BOLD}{max(0, views_remaining)}{Colors.ENDC} ({Colors.OKGREEN}{completion_percent:.1f}% Complete{Colors.ENDC})")
                if views_remaining > 0 and avg_time_per_view > 0:
                    time_eta_seconds = views_remaining * avg_time_per_view
                    time_eta_str = f"{time_eta_seconds // 60:.0f}m {time_eta_seconds % 60:.0f}s" if time_eta_seconds >=60 else f"{time_eta_seconds:.0f}s"
                    print(f"{Colors.OKCYAN}  {EMOJIS['wait']} Estimated Time Remaining (ETR): {Colors.BOLD}{time_eta_str}{Colors.ENDC}")
            else:
                print(f"{Colors.OKGREEN}  {EMOJIS['spinner']} Running in {Colors.BOLD}Continuous Mode{Colors.ENDC}. Press Ctrl+C to stop.")
            print(f"{Colors.OKBLUE}  {EMOJIS['info']} Avg. Time Per View (this session): {Colors.BOLD}{avg_time_per_view:.2f} seconds{Colors.ENDC}")
            print(f"{Colors.GRAY}  {EMOJIS['info']} Total Elapsed Time: {Colors.BOLD}{elapsed_time_str}{Colors.ENDC}")
            print(f"{Colors.HEADER}{'-'*60}{Colors.ENDC}\n")
        # No need to print progress_line again here, it's continuously updated by \r
    # (You can further improve other info-tainment outputs in a similar way.)

    try:
        with ThreadPoolExecutor(max_workers=num_parallel_connections) as executor:
            futures = []
            for link_data in validated_links:
                futures.append(executor.submit(view_worker, link_data, views_per_target_link, tor_ports_to_use, progress_update_handler))
            
            # For continuous mode (views_per_target_link == 0), the workers run until stop_event_global is set.
            # For fixed views, we wait for futures to complete.
            if views_per_target_link > 0:
                # Wait for all submitted tasks to complete
                for future in as_completed(futures):
                    if stop_event_global.is_set(): # If stop was triggered externally
                        break
                    try:
                        future.result() # Retrieve result or catch exceptions from worker
                    except Exception as exc:
                        print(f"{Colors.FAIL}{EMOJIS['error']} A worker thread generated an exception: {exc}{Colors.ENDC}")
            else: # Continuous mode - main thread waits for stop_event_global or all workers to finish unexpectedly
                while not stop_event_global.is_set():
                    if all(f.done() for f in futures): # Check if all workers finished prematurely
                        print(f"{Colors.WARNING}All workers in continuous mode seem tohave finished. Check for errors or if Tor connections were lost.{Colors.ENDC}")
                        stop_event_global.set() # Signal to exit loop cleanly
                        break
                    time.sleep(1) # Keep main thread alive, periodically check stop_event

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}{EMOJIS['pause']} Ctrl+C detected! Sending stop signal to worker threads...{Colors.ENDC}")
        stop_event_global.set()
    except Exception as e:
        print(f"\n{Colors.FAIL}{EMOJIS['error']} An unexpected error occurred in the main execution block: {e}{Colors.ENDC}")
        stop_event_global.set() # Signal workers to stop on any other main error
    finally:
        if not stop_event_global.is_set(): # Ensure stop event is set if loop exited normally (e.g. views completed)
            stop_event_global.set()
        
        print(f"{Colors.OKBLUE}Shutting down worker threads... This may take a few moments.{Colors.ENDC}")
        # The ThreadPoolExecutor's context manager (__exit__) will call executor.shutdown(wait=True)
        # However, workers need to check stop_event_global to terminate gracefully and quickly.
        # Giving a small explicit wait here for workers to react before force shutdown if any are stuck.
        # Note: This explicit wait might be redundant if executor.shutdown(wait=True) is fully effective with event checks in workers.
        all_workers_done_check_start = time.time()
        while any(not f.done() for f in futures) and (time.time() - all_workers_done_check_start < (5 + num_parallel_connections * 0.5)):
            # Wait up to ~5-10s for workers to finish based on connection count
            time.sleep(0.2)
        if any(not f.done() for f in futures):
            print(f"{Colors.WARNING}Some worker threads may not have terminated gracefully. Forced shutdown might occur.{Colors.ENDC}")

    end_time_proc = time.time()
    total_time_taken = end_time_proc - start_time_proc
    
    print(f"\n{Colors.HEADER}{EMOJIS['star']} VIEW GENERATION SESSION ENDED {EMOJIS['star']}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Total views generated in this session: {Colors.BOLD}{completed_views_total}{Colors.ENDC}")
    print(f"Total time taken: {Colors.BOLD}{total_time_taken:.2f} seconds ({total_time_taken/60:.2f} minutes).{Colors.ENDC}")
    if completed_views_total > 0 and total_time_taken > 0:
        print(f"Average time per view: {Colors.BOLD}{total_time_taken/completed_views_total:.2f} seconds.{Colors.ENDC}")

    print(f"\n{Colors.OKBLUE}Summary per link for this session:{Colors.ENDC}")
    if not validated_links: # Should not happen if checks above are correct
        print(f"  {Colors.WARNING}No links were processed.{Colors.ENDC}")
    else:
        for link_data in validated_links:
            views_count = views_per_link_tracker.get(link_data['id'], 0)
            print(f"  - {EMOJIS['link']} {link_data['url'][:60]}... : {Colors.BOLD}{views_count}{Colors.ENDC} views")

    print(f"\n{NEXT_TEXT}")
    print(f"{Colors.OKCYAN}Thank you for using KADDU YT-VIEWS! {EMOJIS['kaddu']}{Colors.ENDC}")

if __name__ == "__main__":
    main()
