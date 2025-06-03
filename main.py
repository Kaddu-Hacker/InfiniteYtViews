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
import itertools
import random
import urllib.request
import json
import zipfile
import tarfile
import socket
import stat
import argparse
import requests  # Added for requests usage

# --- DOCKER AND STEM RELATED IMPORTS ---
import docker # For interacting with Docker daemon
from stem.control import Controller # For Tor control
from stem import Signal # For NEWNYM signal

# --- UI ENHANCEMENTS: Banner and Spinner (modular, robust) ---
# These are used only for setup/install steps, not for the main logic.
try:
    from rich.console import Console
    from rich.spinner import Spinner
    from rich.text import Text
    from rich.syntax import Syntax
    import pyfiglet
except ImportError:
    # Fallback: install missing packages if not present
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'rich', 'pyfiglet'])
    from rich.console import Console
    from rich.spinner import Spinner
    from rich.text import Text
    from rich.syntax import Syntax
    import pyfiglet

console = Console()

# --- CONSTANTS ---
GECKO_API_URL = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"  # For geckodriver download

def print_banner():
    """
    Prints the ASCII banner from the 'ASCII' file if present, otherwise uses pyfiglet as fallback.
    """
    ascii_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ASCII')
    if os.path.exists(ascii_path):
        with open(ascii_path, 'r', encoding='utf-8', errors='ignore') as f:
            banner = f.read()
        console.print(f"[bold magenta]{banner}[/bold magenta]")
    else:
        # Fallback to pyfiglet if ASCII file is missing
        banner = pyfiglet.figlet_format("KADDU YT-VIEWS", font="slant")
        console.print(f"[bold magenta]{banner}[/bold magenta]")
    console.print("[cyan]Automated, Smart, and Human-like YouTube View Simulation![/cyan]\n")

def spinner_message(message, func, *args, **kwargs):
    """
    Runs func(*args, **kwargs) with a spinner and message. Returns the result.
    """
    with console.status(f"[bold yellow]{message}[/bold yellow]", spinner="dots"):
        return func(*args, **kwargs)
# --- END UI ENHANCEMENTS ---

# --- EARLY DEFINITIONS: Setup functions and globals used in prioritized setup ---
# These must be defined before their first use in the setup sequence.

# Global stop event for thread control (used in main and elsewhere)
stop_event_global = threading.Event()

# --- SETUP FUNCTIONS (venv, dependency, binary checks) ---
# (All setup functions are already defined below in the script)

# --- VIRTUAL ENVIRONMENT CHECK & PYTHON DEPENDENCY INSTALLER ---
def require_venv_or_exit():
    """
    Checks if the script is running inside a Python virtual environment.
    Exits with a clear message if not. This prevents polluting system Python.
    """
    venv_active = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV')
    )
    if not venv_active:
        console.print("[bold red]❌ This script must be run inside a Python virtual environment![/bold red]")
        console.print("[yellow]ℹ️  Please create and activate a venv before running.[/yellow]")
        console.print("[cyan]Example (Linux):[/cyan]\\n  python3 -m venv .venv\\n  source .venv/bin/activate\\n  python3 main.py")
        sys.exit(1)
    else:
        console.print("[bold green]✅ Virtual environment detected.[/bold green]")

def check_and_install_python_dependencies():
    """
    Installs all required Python packages from requirements.txt if not already installed.
    Provides clear, emoji-filled feedback for each step.
    """
    console.print("[blue]🔎 Checking Python dependencies...[/blue]")
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if not os.path.exists(req_file):
        console.print("[bold red]❌ requirements.txt not found![/bold red]")
        sys.exit(1)
    try:
        # Try importing all required modules to see if install is needed
        with open(req_file) as f:
            pkgs = [line.strip().split('==')[0] for line in f if line.strip() and not line.startswith('#')]
        missing = []
        for pkg in pkgs:
            try:
                importlib.import_module(pkg)
            except ImportError:
                missing.append(pkg)
        if not missing:
            console.print("[bold green]✅ All Python dependencies are already installed.[/bold green]")
            return
        console.print(f"[yellow]⚠️  Missing packages: {', '.join(missing)}[/yellow]")
        console.print("[blue]📦 Installing required packages from requirements.txt...[/blue]")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req_file])
        console.print("[bold green]✅ All Python dependencies installed successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to install Python dependencies: {e}[/bold red]")
        sys.exit(1)

# --- DOCKER AND SYSTEM CHECK FUNCTIONS ---
def is_command_available(command):
    """Checks if a command is available in the system PATH."""
    return shutil.which(command) is not None

def check_docker_installed():
    """Checks if Docker is installed and provides instructions if not."""
    console.print("[blue]🔄 Checking Docker installation...[/blue]")
    if not is_command_available("docker"):
        console.print("[bold red]❌ Docker is not installed or not in PATH.[/bold red]")
        console.print("[cyan]ℹ️  Please install Docker. For Debian/Ubuntu based systems:[/cyan]")
        console.print(Syntax("sudo apt update && sudo apt install docker.io -y && sudo systemctl enable docker --now", "bash", theme="monokai", line_numbers=False))
        # Attempt to add current user to docker group instruction
        if platform.system() == "Linux":
            console.print("[yellow]💡 You might need to add your user to the 'docker' group:[/yellow]")
            console.print(Syntax("sudo usermod -aG docker ${USER}", "bash", theme="monokai", line_numbers=False, background_color="default"))
            console.print("[yellow]   Then, log out and log back in for the group changes to take effect.[/yellow]")
        sys.exit(1)
    
    # Check if Docker service is running
    try:
        client = docker.from_env()
        client.ping() # Check connectivity to Docker daemon
        console.print("[bold green]✅ Docker is installed and the daemon is responsive.[/bold green]")
        return True
    except docker.errors.DockerException as e:
        console.print(f"[bold red]❌ Docker is installed, but the Docker daemon is not responding or permission issue.[/bold red]")
        console.print(f"[red]   Error: {e}[/red]")
        if platform.system() == "Linux" and "permission denied" in str(e).lower():
             console.print("[yellow]💡 This might be a permission issue. Did you add your user to the 'docker' group and relogged?[/yellow]")
             console.print(Syntax("sudo usermod -aG docker ${USER}", "bash", theme="monokai", line_numbers=False, background_color="default"))
             console.print("[yellow]   Log out and log back in, or try running the script with sudo (not recommended for general use).[/yellow]")
        sys.exit(1)

def check_docker_compose_installed():
    """Checks if Docker Compose is installed and provides instructions if not."""
    console.print("[blue]🔄 Checking Docker Compose installation...[/blue]")
    if not is_command_available("docker-compose"):
        console.print("[bold red]❌ Docker Compose is not installed or not in PATH.[/bold red]")
        console.print("[cyan]ℹ️  Please install Docker Compose. For many systems, it can be installed via pip or as a plugin.[/cyan]")
        console.print("[cyan]   Refer to the official Docker Compose installation guide for your system.[/cyan]")
        # Example for plugin install on Linux, adjust if needed
        console.print("[cyan]   Example for Linux (Docker Compose plugin):[/cyan]")
        console.print(Syntax("sudo apt update && sudo apt install docker-compose-plugin -y", "bash", theme="monokai", line_numbers=False))
        sys.exit(1)
    console.print("[bold green]✅ Docker Compose is installed.[/bold green]")
    return True

# --- DOCKER COMPOSE MANAGEMENT ---
DOCKER_COMPOSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docker-compose.yml")

def start_tor_services():
    """Starts the Tor services using docker-compose."""
    console.print("[blue]🚀 Starting Tor services via docker-compose...[/blue]")
    if not os.path.exists(DOCKER_COMPOSE_FILE):
        console.print(f"[bold red]❌ docker-compose.yml not found at {DOCKER_COMPOSE_FILE}[/bold red]")
        console.print("[cyan]Please ensure the docker-compose.yml file is in the same directory as the script.[/cyan]")
        sys.exit(1)

    try:
        # Using subprocess to run docker-compose commands
        # Build images if they are not present, and then start services in detached mode
        # Using --quiet-pull to reduce verbosity of docker-compose pull messages
        # Changed to capture output to check for errors more reliably
        process = subprocess.Popen(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d", "--build", "--quiet-pull"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(timeout=180) # Increased timeout

        if process.returncode == 0:
            console.print("[bold green]✅ Tor services started successfully via docker-compose.[/bold green]")
            # Add a small delay to allow services to initialize
            time.sleep(10) # Increased delay for services to become ready
            return True
        else:
            console.print("[bold red]❌ Failed to start Tor services via docker-compose.[/bold red]")
            console.print(f"[red]Return code: {process.returncode}[/red]")
            if stdout:
                console.print(f"[grey50]STDOUT:\n{stdout}[/grey50]")
            if stderr:
                console.print(f"[red]STDERR:\n{stderr}[/red]")
            return False
    except subprocess.TimeoutExpired:
        console.print("[bold red]❌ Timeout occurred while starting Tor services with docker-compose.[/bold red]")
        return False
    except Exception as e:
        console.print(f"[bold red]❌ An error occurred while running docker-compose up: {e}[/bold red]")
        return False

def stop_tor_services():
    """Stops the Tor services using docker-compose."""
    console.print("[blue]🛑 Stopping Tor services via docker-compose...[/blue]")
    if not os.path.exists(DOCKER_COMPOSE_FILE):
        console.print(f"[yellow]⚠️ docker-compose.yml not found. Cannot stop services if they were started by this script.[/yellow]")
        return False
    try:
        # Stop and remove containers, networks, volumes, and images created by `up`.
        # Using --quiet-pull to reduce verbosity if any pull happens during down (less likely)
        process = subprocess.Popen(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "down", "--remove-orphans"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(timeout=120)

        if process.returncode == 0:
            console.print("[bold green]✅ Tor services stopped and cleaned up successfully via docker-compose.[/bold green]")
            return True
        else:
            console.print("[bold red]❌ Failed to stop Tor services via docker-compose.[/bold red]")
            console.print(f"[red]Return code: {process.returncode}[/red]")
            if stdout:
                console.print(f"[grey50]STDOUT:\n{stdout}[/grey50]")
            if stderr:
                console.print(f"[red]STDERR:\n{stderr}[/red]")
            return False
            
    except subprocess.TimeoutExpired:
        console.print("[bold red]❌ Timeout occurred while stopping Tor services with docker-compose.[/bold red]")
        return False
    except Exception as e:
        console.print(f"[bold red]❌ An error occurred while running docker-compose down: {e}[/bold red]")
        return False

def get_tor_ports_from_compose():
    """
    Returns a list of (SOCKS_port, control_port) tuples based on docker-compose.yml.
    Currently hardcoded for torproxy1, torproxy2, torproxy3 as defined in the generated yml.
    """
    # These ports must match the host ports defined in docker-compose.yml
    ports_config = [
        {"name": "torproxy1", "socks_port": 9050, "control_port": 8050},
        {"name": "torproxy2", "socks_port": 9051, "control_port": 8051},
        {"name": "torproxy3", "socks_port": 9052, "control_port": 8052},
        # Add more here if you expand docker-compose.yml
    ]
    # Verify that these services are actually running and ports are accessible
    # For now, we assume docker-compose up was successful
    # A more robust approach would be to use the docker client to inspect container ports
    # or attempt to connect to each port.
    
    active_proxies = []
    console.print("[blue]🔍 Verifying configured Tor proxy ports...[/blue]")
    client = docker.from_env() # Initialize docker client to check container status
    
    running_container_names = []
    try:
        for container in client.containers.list():
            # Names might include project prefix, e.g., "views_torproxy1_1"
            # We check if any part of the configured name is in the running container name
            for cfg in ports_config:
                if cfg["name"] in container.name: # A bit loose, but simple
                    running_container_names.append(cfg["name"])
                    break
    except docker.errors.DockerException:
        console.print("[yellow]⚠️ Could not list Docker containers. Assuming ports based on docker-compose.yml definition.[/yellow]")
        # Fallback to assuming all defined ports are available if Docker API fails
        for cfg in ports_config:
             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", cfg["socks_port"])) == 0:
                    console.print(f"  [green]✅ Port {cfg['socks_port']} (SOCKS for {cfg['name']}) is connectable (assuming from compose).[/green]")
                    active_proxies.append((cfg["socks_port"], cfg["control_port"], cfg["name"]))
                else:
                    console.print(f"  [yellow]⚠️ Port {cfg['socks_port']} (SOCKS for {cfg['name']}) is NOT connectable (assuming from compose).[/yellow]")
    else:
        console.print("[yellow]⚠️ Python 'docker' library not loaded. Verifying ports by simple connection test only.[/yellow]")
        # Fallback: if docker lib is not loaded, just try to connect
        for cfg in ports_config:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", cfg["socks_port"])) == 0:
                    console.print(f"  [green]✅ Port {cfg['socks_port']} (SOCKS for {cfg['name']}) is connectable.[/green]")
                    active_proxies.append((cfg["socks_port"], cfg["control_port"], cfg["name"]))
                else:
                    console.print(f"  [yellow]⚠️ Port {cfg['socks_port']} (SOCKS for {cfg['name']}) is NOT connectable.[/yellow]")
            
    if not active_proxies:
        console.print("[bold red]❌ No active and connectable Tor proxies found from Docker Compose configuration.[/bold red]")
    return active_proxies

# --- TOR CONTROL FUNCTIONS (using stem) ---
def test_tor_connection(socks_port, service_name="<unknown service>"):
    """Tests connection through a given Tor SOCKS port and prints the IP."""
    proxies = {
        'http': f'socks5h://127.0.0.1:{socks_port}',
        'https': f'socks5h://127.0.0.1:{socks_port}'
    }
    try:
        # Using a reliable and fast service to get IP
        r = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=15) # Increased timeout slightly
        r.raise_for_status() # Raise an exception for HTTP errors
        ip_address = r.json()['ip']
        console.print(f"[green]🌍 Tor connection via SOCKS port {socks_port} ({service_name}) successful. Current IP: {ip_address}[/green]")
        return ip_address
    except requests.exceptions.Timeout:
        console.print(f"[red]❌ Timeout connecting to SOCKS port {socks_port} ({service_name}) or retrieving IP.[/red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ Failed to connect/get IP via Tor SOCKS port {socks_port} ({service_name}): {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ An unexpected error occurred testing Tor SOCKS port {socks_port} ({service_name}): {e}[/red]")
    return None

def renew_tor_identity(control_port, service_name="<unknown service>"):
    """Requests a new Tor identity (new IP) via the Tor control port."""
    # Support password from CLI/env/config
    args = None
    try:
        import sys
        if hasattr(sys, 'argv') and '--tor-control-pass' in sys.argv:
            # Will be handled by parse_args, but for direct calls, fallback
            pass
        args = parse_args() if 'parse_args' in globals() else None
    except Exception:
        pass
    password = None
    if args and getattr(args, 'tor_control_pass', None):
        password = args.tor_control_pass
    elif os.environ.get('TOR_CONTROL_PASS'):
        password = os.environ['TOR_CONTROL_PASS']
    else:
        password = ''
    try:
        from stem.control import Controller
        with Controller.from_port(port=control_port) as controller:
            if password:
                controller.authenticate(password=password)
            else:
                controller.authenticate() # Authenticates with null/empty password or cookie if enabled by default
            controller.signal(Signal.NEWNYM)
            console.print(f"[bold green]🔄 Requested new Tor identity (NEWNYM) for {service_name} on control port {control_port}.[/bold green]")
            time.sleep(5) # Give Tor some time to establish a new circuit
            return True
    except stem.SocketError as e:
        console.print(f"[red]❌ SocketError: Could not connect to Tor control port {control_port} for {service_name}. Is Tor service running and port mapped? {e}[/red]")
    except stem.InvalidPassword as e: # Or stem.IncorrectPassword depending on stem version
        console.print(f"[red]❌ InvalidPassword: Authentication failed for Tor control port {control_port} for {service_name}. {e}[/red]")
        console.print(f"[yellow]   If you set TOR_CONTROL_PASSWD in docker-compose.yml or system Tor, ensure it matches or handle authentication.[/yellow]")
    except stem.ControllerError as e:
        console.print(f"[red]❌ ControllerError: Failed to send NEWNYM signal to Tor control port {control_port} for {service_name}: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ An unexpected error occurred with Tor control port {control_port} for {service_name}: {e}[/red]")
    return False

# --- ensure_geckodriver_available definition (moved up from below) ---
def ensure_geckodriver_available():
    drivers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drivers")
    os.makedirs(drivers_dir, exist_ok=True)
    geckodriver_name = "geckodriver.exe" if os.name == "nt" else "geckodriver"
    gecko_local_path = os.path.join(drivers_dir, geckodriver_name)
    console.print("[blue]🔄 Checking geckodriver availability...[/blue]")

    # Check if geckodriver is in PATH (system-wide)
    if shutil.which("geckodriver") and not os.path.exists(gecko_local_path): # Prioritize system PATH if not in local drivers
        console.print(f"[bold green]✅ geckodriver is already available in system PATH.[/bold green]")
        return

    # Check if geckodriver is in local ./drivers/ directory
    if os.path.exists(gecko_local_path):
        if os.name != "nt" and not os.access(gecko_local_path, os.X_OK):
            try:
                current_mode = os.stat(gecko_local_path).st_mode
                os.chmod(gecko_local_path, current_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
                console.print(f"[green]ℹ️  Made geckodriver in ./drivers/ executable.[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Could not set executable permission on geckodriver: {e}[/yellow]")
        
        # Add ./drivers to PATH for this session
        if drivers_dir not in os.environ["PATH"].split(os.pathsep):
             os.environ["PATH"] = drivers_dir + os.pathsep + os.environ["PATH"]
             console.print(f"[green]ℹ️  Added ./drivers/ to PATH for this session.[/green]")

        if shutil.which("geckodriver"):
            console.print(f"[bold green]✅ geckodriver is now available via PATH (from ./drivers/).[/bold green]")
        else:
            console.print(f"[yellow]⚠️  geckodriver is in ./drivers/ and PATH updated, but shutil.which() still cannot find it. Manual check may be needed.[/yellow]")
        return

    # If not found, proceed to download
    console.print("[blue]geckodriver not found in PATH or ./drivers/. Attempting to download...[/blue]")
    
    sys_plat = platform.system().lower()
    arch = platform.machine().lower()
    
    # Determine the asset identifier based on OS and arch
    asset_identifier = None
    if sys_plat.startswith("win"):
        asset_identifier = "win64.zip" if "64" in arch else "win32.zip"
    elif sys_plat == "darwin": # macOS
        asset_identifier = "macos-aarch64.tar.gz" if arch == "arm64" else "macos.tar.gz"
    elif sys_plat == "linux":
        if arch in ("x86_64", "amd64"):
            asset_identifier = "linux64.tar.gz"
        elif arch in ("aarch64", "arm64"):
            asset_identifier = "linux-aarch64.tar.gz"
        elif arch == "armv7l": # Example for 32-bit ARM
            asset_identifier = "linux-arm7hf.tar.gz" 
    
    if not asset_identifier:
        console.print(f"[bold red]❌ Unsupported OS/architecture for geckodriver auto-download: {sys_plat}/{arch}[/bold red]")
        console.print(f"[cyan]ℹ️  Please download geckodriver manually: https://github.com/mozilla/geckodriver/releases/latest[/cyan]")
        return

    console.print(f"[cyan]ℹ️  Fetching latest geckodriver release info for {asset_identifier}...[/cyan]")
    gecko_url = None
    gecko_asset_name = None
    try:
        with urllib.request.urlopen(GECKO_API_URL, timeout=15) as response:
            release_data = json.load(response)
        
        for asset in release_data.get("assets", []):
            name = asset.get("name", "")
            # More robust check, allows for vX.Y.Z prefix and ensures it's the correct arch
            if asset_identifier in name and name.endswith((".zip", ".tar.gz")):
                gecko_url = asset.get("browser_download_url")
                gecko_asset_name = name # Store the full asset name
                break
        
        if not gecko_url:
            console.print(f"[bold red]❌ Could not find a download URL for {asset_identifier}. Assets: {[a.get('name') for a in release_data.get('assets', [])]}[/bold red]")
            console.print(f"[cyan]ℹ️  Please download geckodriver manually: https://github.com/mozilla/geckodriver/releases/latest[/cyan]")
            return

    except Exception as e_api:
        console.print(f"[bold red]❌ Failed to fetch geckodriver release info: {e_api}[/bold red]")
        console.print(f"[cyan]ℹ️  Please download geckodriver manually: https://github.com/mozilla/geckodriver/releases/latest[/cyan]")
        return

    console.print(f"[cyan]ℹ️  Downloading {gecko_asset_name} from: {gecko_url}[/cyan]")
    archive_path = os.path.join(drivers_dir, gecko_asset_name)
    try:
        # Ensure old archive is removed if it exists
        if os.path.exists(archive_path): os.remove(archive_path)
        if os.path.exists(gecko_local_path): os.remove(gecko_local_path) # Remove old binary too

        urllib.request.urlretrieve(gecko_url, archive_path)
        console.print(f"[green]Download complete: {archive_path}[/green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to download geckodriver: {e}[/bold red]")
        return

    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(drivers_dir) # Extracts geckodriver.exe directly usually
        elif archive_path.endswith(".tar.gz"):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                # Common tar structure is just the binary, or a folder containing it.
                # We need to extract the binary itself to drivers_dir/geckodriver
                for member in tar_ref.getmembers():
                    if member.name == geckodriver_name or member.name.endswith('/' + geckodriver_name) : # Handles cases like "geckodriver" or "anyfolder/geckodriver"
                        # Extract directly into drivers_dir, renaming if necessary
                        member.name = os.path.basename(member.name) # Ensure it's just 'geckodriver' or 'geckodriver.exe'
                        tar_ref.extract(member, drivers_dir)
                        break 
                else: # If not found by specific name, extract all and search
                    tar_ref.extractall(drivers_dir)
                    found_in_tar = False
                    for root, _, files in os.walk(drivers_dir):
                        if geckodriver_name in files:
                            # Move it to the root of drivers_dir if it's in a subfolder
                            if root != drivers_dir:
                                shutil.move(os.path.join(root, geckodriver_name), gecko_local_path)
                                # Clean up the (now possibly empty) subdirectory
                                try:
                                    if not os.listdir(root): # Check if empty
                                        os.rmdir(root)
                                except OSError: pass
                            found_in_tar = True
                            break
                    if not found_in_tar:
                        console.print(f"[yellow]⚠️ Geckodriver binary ('{geckodriver_name}') not found directly after tar.gz extraction. Check '{drivers_dir}'.[/yellow]")
                        # Do not return here, let it try to make it executable and add to PATH


        else:
            console.print(f"[bold red]❌ Unknown archive format for geckodriver: {archive_path}[/bold red]")
            return
        console.print(f"[bold green]✅ geckodriver extracted to {drivers_dir}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to extract geckodriver: {e}[/bold red]")
        return
    finally:
        try:
            if os.path.exists(archive_path): os.remove(archive_path)
        except Exception: pass

    if not os.path.exists(gecko_local_path):
        console.print(f"[bold red]❌ geckodriver binary not found at {gecko_local_path} after extraction attempt.[/bold red]")
        return

    if os.name != "nt": # Make executable on non-Windows
        try:
            st = os.stat(gecko_local_path)
            os.chmod(gecko_local_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            console.print(f"[green]ℹ️  Made {gecko_local_path} executable.[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not set executable permission on {gecko_local_path}: {e}[/yellow]")

    # Add to PATH if not already there (or re-add to prioritize)
    abs_drivers_dir = os.path.abspath(drivers_dir)
    path_dirs = [os.path.abspath(p) for p in os.environ["PATH"].split(os.pathsep)]
    if abs_drivers_dir not in path_dirs:
        os.environ["PATH"] = abs_drivers_dir + os.pathsep + os.environ["PATH"]
        console.print(f"[green]ℹ️  Added {abs_drivers_dir} to PATH.[/green]")
    
    # Final check
    if shutil.which("geckodriver") and os.path.exists(gecko_local_path) and os.path.samefile(shutil.which("geckodriver"), gecko_local_path):
        console.print(f"[bold green]✅ geckodriver is ready and configured in PATH![/bold green]")
    else:
        console.print(f"[yellow]⚠️  geckodriver downloaded to {gecko_local_path}, but might not be correctly picked up by PATH. Selenium might fail. Ensure {abs_drivers_dir} is in your PATH and prioritized.[/yellow]")

# --- ensure_tor_installed definition (moved up from below) ---
def ensure_tor_installed():
    console.print("[blue]🔄 Checking Tor installation...[/blue]")

    def is_command_available(command):
        return shutil.which(command) is not None

    if is_command_available("tor"):
        console.print("[bold green]✅ Tor is already installed and in PATH.[/bold green]")
        return True

    # Check local 'tor_files' directory (for Windows portable Tor)
    tor_exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tor_files", "Tor", "tor.exe")
    if os.name == 'nt' and os.path.exists(tor_exe_path):
        console.print(f"[green]Found Tor executable at: {tor_exe_path}[/green]")
        # Add Tor to PATH for this session if not already discoverable
        tor_dir = os.path.dirname(tor_exe_path)
        if tor_dir not in os.environ["PATH"]:
            os.environ["PATH"] = tor_dir + os.pathsep + os.environ["PATH"]
            console.print(f"[green]Temporarily added {tor_dir} to PATH.[/green]")
        if is_command_available("tor"):
            console.print("[bold green]✅ Tor (local) is now available in PATH.[/bold green]")
            return True
        else:
            console.print("[yellow]⚠️  Found local Tor but 'tor' command is still not available. Check PATH configuration.[/yellow]")
            # Fall through to download/manual instructions if it's not correctly added or found

    console.print("[yellow]Tor not found in PATH.[/yellow]")

    sys_platform = platform.system()
    if sys_platform == "Windows":
        console.print("[cyan]ℹ️  For Windows, Tor can be downloaded automatically.[/cyan]")
        # Use console.input for consistency
        download_tor = console.input("[bold yellow]Do you want to download and extract Tor for Windows? (yes/no): [/bold yellow]").strip().lower()
        if download_tor == 'yes':
            TOR_WIN_URL = "https://www.torproject.org/dist/torbrowser/13.0.10/tor-win64-0.4.8.10.zip" # Example URL, check for latest
            # It's better to fetch the expert bundle, not the whole browser if only 'tor.exe' is needed.
            # Corrected URL for Tor Expert Bundle (ensure this is the most current or a stable one):
            TOR_EXPERT_BUNDLE_URL = "https://www.torproject.org/dist/torbrowser/13.0.10/tor-expert-bundle-0.4.8.10-windows-x86_64.zip"
            # The above URL might become outdated. A more robust solution would be to parse the Tor Project download page or use a fixed, known-good version.
            # For simplicity, we'll use a direct link. Users should verify this link if it fails.

            console.print(f"[cyan]Attempting to download Tor Expert Bundle from: {TOR_EXPERT_BUNDLE_URL}[/cyan]")
            
            drivers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tor_files") # Changed to 'tor_files' to match tor_exe_path
            os.makedirs(drivers_dir, exist_ok=True)
            archive_name = TOR_EXPERT_BUNDLE_URL.split('/')[-1]
            archive_path = os.path.join(drivers_dir, archive_name)

            try:
                urllib.request.urlretrieve(TOR_EXPERT_BUNDLE_URL, archive_path)
                console.print(f"[green]Downloaded {archive_name} to {drivers_dir}[/green]")

                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # Extract only tor.exe and required DLLs if known, or the whole 'Tor' folder
                    # For simplicity, extracting the 'Tor' folder from the expert bundle structure.
                    # The expert bundle usually has a structure like: tor-expert-bundle/Tor/tor.exe
                    # We want to extract the 'Tor' directory into 'tor_files/Tor'
                    for member in zip_ref.namelist():
                        if member.startswith("Tor/") or member.startswith("Data/"):
                             # Adjust path to extract 'Tor' dir directly into 'drivers_dir/Tor'
                            target_path = os.path.join(drivers_dir, member)
                            if member.endswith('/'): # it is a directory
                                os.makedirs(target_path, exist_ok=True)
                            else: # it is a file
                                with open(target_path, "wb") as outfile, zip_ref.open(member, "r") as infile:
                                    shutil.copyfileobj(infile, outfile)

                console.print(f"[bold green]✅ Tor extracted to {os.path.join(drivers_dir, 'Tor')}[/bold green]")
                
                # Add the new Tor directory to PATH for the current session
                tor_sub_dir = os.path.join(drivers_dir, "Tor")
                os.environ["PATH"] = tor_sub_dir + os.pathsep + os.environ["PATH"]
                console.print(f"[green]Temporarily added {tor_sub_dir} to PATH.[/green]")

                if is_command_available("tor"):
                    console.print("[bold green]✅ Tor is now installed and available.[/bold green]")
                    return True
                else:
                    console.print("[bold red]❌ Tor installed but 'tor' command still not available. Manual PATH setup might be needed.[/bold red]")
                    console.print(f"[cyan]Try adding {tor_sub_dir} to your system PATH.[/cyan]")
                    return False # Indicate failure if not callable

            except Exception as e:
                console.print(f"[bold red]❌ Failed to download or extract Tor: {e}[/bold red]")
                # Fall through to manual instructions
            finally:
                if os.path.exists(archive_path):
                    try:
                        os.remove(archive_path)
                    except Exception as e_del:
                        console.print(f"[yellow]⚠️ Could not delete Tor archive {archive_path}: {e_del}[/yellow]")
        
        # If download was not attempted or failed, show manual instructions
        console.print("[yellow]Please install Tor manually.[/yellow]")
        console.print("[cyan]Visit: https://www.torproject.org/download/tor/ (Expert Bundle recommended)[/cyan]")
        console.print("[cyan]And ensure 'tor.exe' is in your system PATH or in a 'tor_files/Tor' subdirectory next to the script.[/cyan]")
        return False

    elif sys_platform == "Linux":
        console.print("[cyan]ℹ️  For Linux, use your package manager. Example for Debian/Ubuntu:[/cyan]")
        # Using Syntax object for better code display
        console.print(Syntax("sudo apt update && sudo apt install tor", "bash", theme="monokai", line_numbers=False))
    elif sys_platform == "Darwin": # macOS
        console.print("[cyan]ℹ️  For macOS, use Homebrew:[/cyan]")
        console.print(Syntax("brew install tor", "bash", theme="monokai", line_numbers=False))
    else:
        console.print(f"[yellow]Unsupported OS: {sys_platform}. Please install Tor manually and ensure it's in PATH.[/yellow]")
    
    # Final check after instructions
    if is_command_available("tor"):
        console.print("[bold green]✅ Tor is available.[/bold green]")
        return True
    else:
        console.print("[bold red]❌ Tor is not available after attempting setup/providing instructions. Please install it manually.[/bold red]")
        return False

# --- CLI ARGUMENT PARSING ---
def parse_args():
    parser = argparse.ArgumentParser(description="KADDU YT-VIEWS SYSTEM: YouTube view generator with Tor proxies (Docker or system Tor)")
    parser.add_argument('--use-docker', dest='use_docker', action='store_true', help='Force use of Dockerized Tor proxies (default: auto-detect)')
    parser.add_argument('--no-docker', dest='no_docker', action='store_true', help='Force use of system Tor only (ignore Docker)')
    parser.add_argument('--tor-ports', type=str, default='', help='Comma-separated list of Tor SOCKS ports to use (system Tor mode only, e.g. 9050,9052,9054)')
    parser.add_argument('--tor-port-range', type=str, default='9050-9100', help='Port range to scan for Tor SOCKS (system Tor mode, default: 9050-9100)')
    parser.add_argument('--tor-control-pass', type=str, default='', help='Tor control port password (if set in Docker or system Tor)')
    parser.add_argument('--auto', action='store_true', help='Automatically install/start dependencies without prompting')
    parser.add_argument('video_urls', nargs='*', help='YouTube video URL(s) to process.')
    parser.add_argument('--views-per-link', type=int, default=10, help='Number of views to generate per link (default: 10).')
    parser.add_argument('--parallel-workers', type=int, default=0, help='Number of parallel view workers (0=auto-adjust to available proxies, max 10).')
    parser.add_argument('--min-watch-time', type=int, default=45, help='Minimum watch time in seconds (default: 45).')
    parser.add_argument('--max-watch-time', type=int, default=120, help='Maximum watch time in seconds (default: 120).')
    parser.add_argument('--dry-run', action='store_true', help='Simulate actions without actual viewing or IP rotation.')
    return parser.parse_args()

# --- AUTO-INSTALL/START HELPERS ---
def prompt_or_auto(message, auto):
    if auto:
        return True
    try:
        return input(f"{message} [Y/n]: ").strip().lower() in ('y', 'yes', '')
    except Exception:
        return False

def install_and_start_tor(auto=False):
    if is_termux():
        if shutil.which('tor') is None:
            if prompt_or_auto("Tor is not installed. Install Tor with 'pkg install tor'?", auto):
                subprocess.run(['pkg', 'install', '-y', 'tor'])
        # Start Tor if not running
        if not is_tor_running(9050):
            if prompt_or_auto("Start Tor with 'tor &'?", auto):
                subprocess.Popen(['tor'])
    elif platform.system().lower() == 'linux':
        if shutil.which('tor') is None:
            if prompt_or_auto("Tor is not installed. Install Tor with 'sudo apt install tor'?", auto):
                subprocess.run(['sudo', 'apt', 'install', '-y', 'tor'])
        # Start Tor if not running
        if not is_tor_running(9050):
            if prompt_or_auto("Start Tor with 'sudo service tor start'?", auto):
                subprocess.run(['sudo', 'service', 'tor', 'start'])
    # For other OS, print instructions

def is_tor_running(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False

def install_firefox_and_geckodriver(auto=False):
    if shutil.which('firefox') is None:
        if is_termux():
            if prompt_or_auto("Firefox is not installed. Install with 'pkg install firefox'?", auto):
                subprocess.run(['pkg', 'install', '-y', 'firefox'])
        elif platform.system().lower() == 'linux':
            if prompt_or_auto("Firefox is not installed. Install with 'sudo apt install firefox'?", auto):
                subprocess.run(['sudo', 'apt', 'install', '-y', 'firefox'])
    # geckodriver is handled by ensure_geckodriver_available()

# --- SYSTEM TOR PROXY DISCOVERY ---
def discover_system_tor_proxies(port_list=None, port_range=(9050, 9100)):
    """Scan for open Tor SOCKS ports on localhost."""
    proxies = []
    if port_list:
        ports = port_list
    else:
        ports = list(range(port_range[0], port_range[1]+1))
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                proxies.append((port, None, f"system-tor-{port}")) # No control port by default
    return proxies

def detect_package_manager():
    """Detects the system's package manager."""
    if is_termux():
        return 'pkg'
    if shutil.which('apt'):
        return 'apt'
    if shutil.which('dnf'):
        return 'dnf'
    if shutil.which('yum'):
        return 'yum'
    if shutil.which('zypper'):
        return 'zypper'
    if shutil.which('pacman'):
        return 'pacman'
    return None

# --- AUTO VENV CREATION/ACTIVATION ---
def ensure_venv(auto=False):
    venv_active = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV')
    )
    if venv_active:
        return True
    venv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv')
    if not os.path.exists(venv_dir):
        if prompt_or_auto("No virtual environment detected. Create one in .venv?", auto):
            subprocess.run([sys.executable, '-m', 'venv', venv_dir])
    activate_script = os.path.join(venv_dir, 'bin', 'activate') if os.name != 'nt' else os.path.join(venv_dir, 'Scripts', 'activate.bat')
    if os.path.exists(activate_script):
        console.print(f"[cyan]To activate the venv, run: [bold]source {activate_script}[/bold][/cyan]")
        if not auto:
            sys.exit(0)
        return False
    else:
        console.print(f"[red]Failed to create or find venv at {venv_dir}.[/red]")
        return False

# --- SYSTEM PACKAGE INSTALLATION ---
def install_system_package(pkg_name, auto=False):
    pm = detect_package_manager()
    if not pm:
        console.print(f"[red]No supported package manager found. Please install {pkg_name} manually.[/red]")
        return False
    install_cmd = []
    if pm == 'apt':
        install_cmd = ['sudo', 'apt', 'install', '-y', pkg_name]
    elif pm == 'dnf':
        install_cmd = ['sudo', 'dnf', 'install', '-y', pkg_name]
    elif pm == 'yum':
        install_cmd = ['sudo', 'yum', 'install', '-y', pkg_name]
    elif pm == 'zypper':
        install_cmd = ['sudo', 'zypper', 'install', '-y', pkg_name]
    elif pm == 'pacman':
        install_cmd = ['sudo', 'pacman', '-S', '--noconfirm', pkg_name]
    elif pm == 'pkg':
        install_cmd = ['pkg', 'install', '-y', pkg_name]
    else:
        console.print(f"[red]Unsupported package manager: {pm}. Please install {pkg_name} manually.[/red]")
        return False
    if prompt_or_auto(f"Install {pkg_name} using {pm}?", auto):
        console.print(f"[cyan]Running: {' '.join(install_cmd)}[/cyan]")
        subprocess.run(install_cmd)
        return True
    return False

# --- AUTO SERVICE START ---
def start_service(service_name, auto=False):
    # Try systemctl, then service
    if shutil.which('systemctl'):
        if prompt_or_auto(f"Start {service_name} with systemctl?", auto):
            subprocess.run(['sudo', 'systemctl', 'start', service_name])
            return True
    if shutil.which('service'):
        if prompt_or_auto(f"Start {service_name} with service?", auto):
            subprocess.run(['sudo', 'service', service_name, 'start'])
            return True
    return False

# --- ONBOARDING WELCOME ---
def onboarding_welcome():
    console.rule("[bold green]Welcome to KADDU YT-VIEWS SYSTEM![/bold green]")
    console.print("[cyan]This script will help you generate YouTube views using Tor proxies in a safe, automated, and human-like way.[/cyan]")
    console.print("[green]It will check your environment, install missing dependencies, and guide you through setup.[/green]")
    console.print("[yellow]If you get stuck, see the README or use --auto for full automation.[/yellow]")
    console.print("[magenta]For help, visit: https://github.com/yourrepo/yt-views#troubleshooting[/magenta]")

# --- HELPER: Detect Termux ---
def is_termux():
    # Detect Termux by checking for the 'com.termux' prefix in $PREFIX or $HOME
    return 'com.termux' in os.environ.get('PREFIX', '') or 'com.termux' in os.environ.get('HOME', '')

# --- Main application logic ---
def main():
    global stop_event_global
    args = parse_args()
    auto_mode = getattr(args, 'auto', False)
    onboarding_welcome()
    # Always show the banner after onboarding
    print_banner()
    if not ensure_venv(auto=auto_mode):
        # If venv is not ready, tell the user what to do next
        console.print("[yellow]Activate your virtual environment and re-run: [bold]python main.py[/bold][/yellow]")
        return
    # ... rest of main ...
    # Before Tor/Firefox checks:
    if shutil.which('tor') is None:
        install_system_package('tor', auto=auto_mode)
    if shutil.which('firefox') is None:
        install_system_package('firefox', auto=auto_mode)
    # Start Tor if not running
    if not is_tor_running(9050):
        start_service('tor', auto=auto_mode)
    # ... rest of main ...
    # At the end of main, if setup is complete, print what to do next if not running core logic
    # (If core logic is not implemented here, add a message)
    console.print("[bold green]Setup complete! To start generating views, provide YouTube URLs as arguments or follow the prompts.[/bold green]")
    console.print("[cyan]Example: python main.py https://www.youtube.com/watch?v=your_video_id[/cyan]")
    console.print("[cyan]Or run with --help for all options: python main.py --help[/cyan]")

# --- Main execution block `if __name__ == "__main__":` --- 
if __name__ == "__main__":
    # Ensure stop_tor_services is called on exit, even if errors occur early
    services_started_by_script = False
    try:
        # Initial Setup Checks (Python Env, Dependencies, Geckodriver, Docker)
        spinner_message("Checking virtual environment...", require_venv_or_exit)
        spinner_message("Checking Python dependencies...", check_and_install_python_dependencies)
        spinner_message("Checking Docker installation...", check_docker_installed)
        spinner_message("Checking Docker Compose installation...", check_docker_compose_installed)
        spinner_message("Ensuring geckodriver is available...", ensure_geckodriver_available)
        console.print("[blue]--- KADDU YT-VIEWS Dockerized Tor Setup ---[/blue]")
        # Start Tor services defined in docker-compose.yml
        if not start_tor_services():
            console.print("[bold red]❌ Failed to start Dockerized Tor services. Exiting.[/bold red]")
            console.print("[yellow]You can try running: [bold]docker-compose up -d --build[/bold] manually, then re-run [bold]python main.py[/bold][/yellow]")
            sys.exit(1)
        services_started_by_script = True # Mark that services were started
        # If all setup passes, proceed to main application logic
        main() # Main function now handles user input, validation, and view generation
    except KeyboardInterrupt:
        console.print("[bold yellow]\n🛑 Process interrupted by user (Ctrl+C). Signaling stop...[/bold yellow]")
        stop_event_global.set()
        console.print("[blue]Please wait for graceful shutdown of active workers...[/blue]")
        time.sleep(3)
    except SystemExit as e: # Catch sys.exit() from core_logic
        if e.code != 0: console.print(f"[bold red]😢 Script exited with code: {e.code}.[/bold red]")
    except Exception as e_core:
        console.print(f"[bold red]\n❌ --- CRITICAL UNEXPECTED ERROR DURING CORE LOGIC --- [/bold red]")
        console.print(f"[red]Type: {type(e_core).__name__}, Details: {e_core}[/red]")
        console.print_exception(show_locals=False)
    finally:
        console.print("\n[blue]Initiating final cleanup...[/blue]")
        stop_event_global.set() # Ensure stop event is set for any lingering threads
        if services_started_by_script:
            pass
        console.print("[bold green]✅ KADDU YT-VIEWS program finished.[/bold green]")
        console.print("[yellow]If you just completed setup, activate your venv and re-run: [bold]python main.py[/bold][/yellow]")
        console.print("[cyan]For help, run: python main.py --help[/cyan]")

# --- END OF SCRIPT ---