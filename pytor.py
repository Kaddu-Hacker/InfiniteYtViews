# NOTE: This file is now always imported after all dependencies and Tor are ensured by main.py.
# No need to check for dependencies or Tor installation here. Only provide Tor/IP utility functions.

import os
import sys
import time
import subprocess
import random
import re
import socket
import requests
import tempfile
import shutil
import signal

# --- GLOBAL EMOJIS AND COLORS (Used by functions in this file) ---
EMOJI_SUCCESS = "✅"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_INFO = "ℹ️"
EMOJI_WAIT = "⏳"
EMOJI_DETECT = "🔎"
EMOJI_START_UP = "🚀"
EMOJI_CHECK = "✔️"
EMOJI_NETWORK = "🌐"
EMOJI_RELOAD = "🔄"

C_GREEN = "\033[1;32m"
C_YELLOW = "\033[1;33m"
C_RED = "\033[1;31m"
C_BLUE = "\033[1;34m"
C_RESET = "\033[0m"
# --- END GLOBAL EMOJIS AND COLORS ---

# --- Default Tor SOCKS and Control Ports ---
DEFAULT_TOR_PORT = 9050
DEFAULT_CONTROL_PORT = 9051 # Though not explicitly used for control in new instances yet

# --- INFOTAINMENT SYSTEM ---
INFOTAINMENT_MESSAGES = [
    "Did you know? The first Tor onion service was launched in 2004!",
    "Fun Fact: Tor bounces your traffic through at least 3 relays for privacy.",
    "Motivation: Every new IP is a new opportunity!",
    "Joke: Why did the onion cry? Because it was peeled by Tor!",
    "Tip: Stay curious—explore the world of privacy tech!",
    "Quote: 'Privacy is not an option, and it shouldn't be the price we accept for just getting on the Internet.'",
    "Trivia: The Tor logo is an onion because of its layered encryption!",
    "Encouragement: You're making the internet a more private place!",
    "Did you know? Tor is used by millions of people every day!",
    "Fun Fact: The Tor network is run by volunteers worldwide!"
]

def print_infotainment():
    msg = random.choice(INFOTAINMENT_MESSAGES)
    print(f"{C_YELLOW}{EMOJI_INFO} [Infotainment] {msg}{C_RESET}")

# --------------------------------------------------------------------------
# Helper Utilities
# --------------------------------------------------------------------------

def is_command_available(command):
    """Checks if a command is available in the system's PATH."""
    return shutil.which(command) is not None

def ensure_tor_binary():
    """
    Checks if the 'tor' binary is available. Exits if not found.
    This is critical before attempting to start new Tor instances.
    """
    print_infotainment()
    print(f"{C_BLUE}{EMOJI_DETECT} Checking for Tor binary...{C_RESET}")
    if not is_command_available("tor"):
        print(f"{C_RED}{EMOJI_ERROR} CRITICAL: 'tor' command not found in PATH.{C_RESET}")
        print(f"{C_YELLOW}{EMOJI_INFO} Please install Tor (e.g., 'sudo apt install tor').{C_RESET}")
        print(f"{C_YELLOW}{EMOJI_INFO} This script needs the 'tor' executable to manage dynamic Tor instances.{C_RESET}")
        sys.exit(1)
    print(f"{C_GREEN}{EMOJI_SUCCESS} 'tor' binary found.{C_RESET}")

# --------------------------------------------------------------------------
# System Tor Service Management (Legacy/Optional)
# These functions interact with a system-wide Tor service.
# Their usage might be deprioritized in favor of user-space instances.
# --------------------------------------------------------------------------

def start_tor():
    """
    Starts the SYSTEM Tor service using various system-specific methods.
    This is for a system-wide Tor, not user-space instances.
    """
    print_infotainment()
    print(f"{C_YELLOW}{EMOJI_WAIT} Attempting to start SYSTEM Tor service...{C_RESET}")
    methods = [
        {"check": ["systemctl", "is-active", "--quiet", "tor"], "start": ["sudo", "systemctl", "start", "tor"], "name": "systemctl"},
        {"check": ["service", "tor", "status"], "start": ["sudo", "service", "tor", "start"], "name": "service"},
        {"check": ["rc-service", "tor", "status"], "start": ["sudo", "rc-service", "tor", "start"], "name": "rc-service"},
    ]
    try:
        pgrep_check = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if pgrep_check.returncode == 0 and pgrep_check.stdout.strip():
            print(f"{C_GREEN}{EMOJI_CHECK} A Tor process is already running (pgrep). Assuming system service or pre-existing.{C_RESET}")
            return True # Indicate a Tor process is running
    except FileNotFoundError:
        print(f"{C_YELLOW}{EMOJI_WARNING} pgrep not found. Cannot perform initial check for running Tor.{C_RESET}")

    for method in methods:
        if not is_command_available(method["start"][0]): continue # Skip if sudo/service command itself is missing
        try:
            print(f"{C_BLUE}{EMOJI_DETECT} Checking system Tor status via '{method['name']}'...{C_RESET}")
            check_result = subprocess.run(method["check"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if check_result.returncode == 0:
                print(f"{C_GREEN}{EMOJI_CHECK} System Tor service is already running ({method['name']}).{C_RESET}")
                return True

            print(f"{C_BLUE}{EMOJI_START_UP} Attempting to start system Tor via '{method['name']}'...{C_RESET}")
            start_result = subprocess.run(method["start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if start_result.returncode == 0:
                print(f"{C_YELLOW}{EMOJI_WAIT} Waiting for system Tor to initialize (10s)...{C_RESET}")
                time.sleep(10)
                verify_pgrep = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                if verify_pgrep.returncode == 0 and verify_pgrep.stdout.strip():
                    print(f"{C_GREEN}{EMOJI_SUCCESS} System Tor service started successfully ({method['name']}).{C_RESET}")
                    return True
                else:
                    print(f"{C_YELLOW}{EMOJI_WARNING} System Tor asked to start ({method['name']}), but pgrep verification failed.{C_RESET}")
            else:
                err_out = start_result.stderr.decode(errors='ignore').strip()
                print(f"{C_RED}{EMOJI_ERROR} Failed to start system Tor with '{method['name']}'. Error: {err_out if err_out else 'Unknown'}{C_RESET}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"{C_YELLOW}{EMOJI_WARNING} Method '{method['name']}' for system Tor failed: {e}{C_RESET}")
    print(f"{C_RED}{EMOJI_ERROR} All methods to start SYSTEM Tor service failed.{C_RESET}")
    return False

# --------------------------------------------------------------------------
# IP Address and Geolocation Utilities
# --------------------------------------------------------------------------

def get_ip(tor_port=DEFAULT_TOR_PORT, verbose=True):
    """
    Fetches current external IP via Tor SOCKS proxy. Returns IP string or None.
    """
    urls = ["https://checkip.amazonaws.com", "https://api.ipify.org", "https://icanhazip.com"]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    proxies = {"http": f"socks5h://127.0.0.1:{tor_port}", "https": f"socks5h://127.0.0.1:{tor_port}"}
    timeout = 7

    for i, url_to_try in enumerate(urls):
        try:
            if verbose: print(f"{C_BLUE}{EMOJI_WAIT} Fetching IP via Tor (Port: {tor_port}, Service: {url_to_try.split('//')[1]})...{C_RESET}", end='\r')
            response = requests.get(url_to_try, headers=headers, proxies=proxies, timeout=timeout)
            response.raise_for_status()
            ip_address = response.text.strip()
            if not re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip_address):
                raise ValueError("Invalid IP format")
            if verbose: 
                sys.stdout.write(" " * 80 + "\r") # Clear line
                print(f"{C_GREEN}{EMOJI_SUCCESS} IP via Tor (Port: {tor_port}):{C_RESET} {ip_address} ({EMOJI_NETWORK} {url_to_try.split('//')[1]}){C_RESET}")
            return ip_address
        except (requests.exceptions.RequestException, ValueError) as e:
            if verbose and not any(isinstance(e, err_type) for err_type in [requests.exceptions.ConnectTimeout, requests.exceptions.ProxyError, requests.exceptions.ConnectionError]):
                sys.stdout.write(" " * 80 + "\r")
                print(f"{C_YELLOW}{EMOJI_WARNING} Service {url_to_try.split('//')[1]} (Port {tor_port}) failed: {type(e).__name__}{C_RESET}")
            if isinstance(e, (requests.exceptions.ProxyError, requests.exceptions.ConnectionError)):
                return None # Port likely inactive
    if verbose: 
        sys.stdout.write(" " * 80 + "\r")
        print(f"{C_RED}{EMOJI_ERROR} All IP services failed for Tor port {tor_port}.{C_RESET}")
    return None

def show_ip_location(ip_address):
    """
    Fetches and displays geolocation for an IP address.
    """
    if not ip_address: print(f"{C_YELLOW}{EMOJI_WARNING} No IP to show location.{C_RESET}"); return
    print(f"{C_BLUE}{EMOJI_DETECT} Geolocation for IP: {ip_address}...{C_RESET}")
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=10)
        response.raise_for_status(); data = response.json()
        print(f"{C_GREEN}{EMOJI_NETWORK} IP Geolocation:{C_RESET} City: {data.get('city', 'N/A')}, Region: {data.get('region', 'N/A')}, Country: {data.get('country', 'N/A')}, ISP: {data.get('org', 'N/A')}")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"{C_RED}{EMOJI_ERROR} Could not fetch/parse geolocation: {e}{C_RESET}")

# --------------------------------------------------------------------------
# User-Space Tor Instance Management (NEW as per guide)
# --------------------------------------------------------------------------

def detect_tor_ports(start_port=9050, end_port=9100, verbose_scan=False):
    """
    Identifies active Tor SOCKS ports by attempting to fetch an IP through them.
    """
    print_infotainment()
    available_ports = []
    print(f"{C_BLUE}{EMOJI_DETECT} Scanning for existing Tor SOCKS ports ({start_port}-{end_port})...{C_RESET}")
    for port in range(start_port, end_port + 1):
        current_ip = get_ip(port, verbose=verbose_scan)
        if current_ip:
            print(f"{C_GREEN}{EMOJI_SUCCESS} Active Tor SOCKS port detected: {port} (IP: {current_ip}){C_RESET}")
            available_ports.append(port)
        elif not verbose_scan: print(f".", end='', flush=True)
    if not verbose_scan: print() # Newline after dots
    if not available_ports: print(f"{C_YELLOW}{EMOJI_WARNING} No active Tor SOCKS ports found in range {start_port}-{end_port}.{C_RESET}")
    else: print(f"{C_GREEN}{EMOJI_SUCCESS} Detection complete. Active ports: {available_ports}{C_RESET}")
    return available_ports

def find_free_ports(num_ports_needed, start_search_port=9101):
    """
    Finds a specified number of free TCP ports for new Tor instances.
    """
    print_infotainment()
    free_ports_found = []
    current_port = start_search_port
    max_search_range = 100 # Limit search to 100 ports beyond start_search_port
    end_search_port = start_search_port + max_search_range
    print(f"{C_BLUE}{EMOJI_DETECT} Searching for {num_ports_needed} free port(s) from {start_search_port} to {end_search_port-1}...{C_RESET}")
    
    temp_socket = None
    while len(free_ports_found) < num_ports_needed and current_port < end_search_port:
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            temp_socket.bind(("127.0.0.1", current_port))
            free_ports_found.append(current_port)
            # print(f"{C_GREEN}{EMOJI_CHECK} Port {current_port} is free.{C_RESET}") # Optional: too verbose
        except (OSError, PermissionError):
            pass # Port in use or other issue
        finally:
            if temp_socket: temp_socket.close()
        current_port += 1
    
    if len(free_ports_found) < num_ports_needed:
        print(f"{C_RED}{EMOJI_ERROR} Could not find {num_ports_needed} free port(s) in range {start_search_port}-{end_search_port-1}. Found: {free_ports_found}{C_RESET}")
    else:
        print(f"{C_GREEN}{EMOJI_SUCCESS} Found {len(free_ports_found)} free port(s): {free_ports_found}{C_RESET}")
    return free_ports_found

def start_tor_instance(port):
    """
    Starts a new Tor instance on a specified port with its own data directory.
    """
    print_infotainment()
    try:
        data_dir = tempfile.mkdtemp(prefix=f"kaddu_tor_{port}_")
    except Exception as e:
        print(f"{C_RED}{EMOJI_ERROR} Failed to create temp data_dir for Tor port {port}: {e}{C_RESET}")
        return None

    pid_file = os.path.join(data_dir, "tor.pid")
    log_file = os.path.join(data_dir, "tor_messages.log")
    cmd = [
        "tor", "--SocksPort", str(port),
        "--DataDirectory", data_dir, "--PidFile", pid_file,
        "--Log", f"notice file {log_file}", "--CookieAuthentication", "0",
        # Essential for user-space instances to avoid conflicting with system Tor or other instances:
        "--ControlPort", "auto", # Let Tor pick a control port
        "--AvoidDiskWrites", "1", # Good for temp instances
        "--ShutdownWaitLength", "0", # Faster shutdown
        # "--quiet" # Might suppress useful errors during startup; log file should capture anyway
    ]
    try:
        log_fp = open(log_file, "a")
        process = subprocess.Popen(cmd, stdout=log_fp, stderr=subprocess.STDOUT)
        print(f"{C_BLUE}{EMOJI_START_UP} Starting Tor instance: Port {port}, PID {process.pid}, DataDir {data_dir}{C_RESET}")
        return {"port": port, "process": process, "data_dir": data_dir, "pid_file": pid_file, "log_file": log_file, "log_fp": log_fp}
    except FileNotFoundError:
        print(f"{C_RED}{EMOJI_ERROR} 'tor' command not found. Cannot start new Tor instance.{C_RESET}")
        if os.path.exists(data_dir): shutil.rmtree(data_dir)
        return None
    except Exception as e:
        print(f"{C_RED}{EMOJI_ERROR} Failed to start Tor instance on port {port}: {e}{C_RESET}")
        if 'log_fp' in locals() and log_fp: log_fp.close()
        if os.path.exists(data_dir): shutil.rmtree(data_dir)
        return None

def verify_tor_instance(instance_info, timeout=90):
    """
    Verifies if a Tor instance is bootstrapped and operational.
    """
    print_infotainment()
    if not instance_info: return False
    start_time = time.time(); log_file = instance_info["log_file"]; port = instance_info["port"]; process = instance_info["process"]
    print(f"{C_YELLOW}{EMOJI_WAIT} Verifying Tor instance (Port {port}, PID {process.pid}). Bootstrap (max {timeout}s)...{C_RESET}")
    bootstrapped_log_msg = "Bootstrapped 100% (done)"
    bootstrapped = False
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            print(f"{C_RED}{EMOJI_ERROR} Tor (Port {port}, PID {process.pid}) terminated. Code: {process.returncode}{C_RESET}")
            try:
                with open(log_file, "r") as f_log: log_tail = f_log.read()
                if log_tail.strip(): print(f"{C_YELLOW}  Log ({log_file}):\n{log_tail[-500:]}{C_RESET}")
            except Exception: pass
            return False
        try:
            with open(log_file, "r") as f:
                if bootstrapped_log_msg in f.read():
                    print(f"{C_GREEN}{EMOJI_CHECK} Tor (Port {port}) bootstrapped. Verifying IP...{C_RESET}")
                    bootstrapped = True; break
        except Exception: pass # File might not exist yet or read error
        time.sleep(2)
    if not bootstrapped:
        print(f"{C_RED}{EMOJI_ERROR} Tor (Port {port}, PID {process.pid}) did NOT bootstrap in {timeout}s.{C_RESET}")
        if process.poll() is None: print(f"{C_YELLOW}  Process still running. Check logs in {instance_info['data_dir']}{C_RESET}")
        return False
    if get_ip(port, verbose=True):
        print(f"{C_GREEN}{EMOJI_SUCCESS} Tor instance (Port {port}) operational.{C_RESET}")
        return True
    else:
        print(f"{C_RED}{EMOJI_ERROR} Tor (Port {port}) bootstrapped, but FAILED to fetch IP.{C_RESET}")
        return False

def change_ip(instance_info):
    """
    Changes IP for a specific Tor instance via SIGHUP.
    """
    if not instance_info or not all(k in instance_info for k in ["pid_file", "port", "process"]):
        print(f"{C_RED}{EMOJI_ERROR} Invalid instance_info to change_ip.{C_RESET}"); return None
    pid_file = instance_info["pid_file"]; port = instance_info["port"]; process_obj = instance_info["process"]
    print(f"{C_YELLOW}{EMOJI_RELOAD} Requesting new circuit for Tor instance (Port {port})...{C_RESET}")
    pid_to_signal = process_obj.pid if process_obj and process_obj.poll() is None else None
    if not pid_to_signal and os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f: pid_to_signal = int(f.read().strip())
        except Exception: pass
    if not pid_to_signal or pid_to_signal <= 0:
        print(f"{C_RED}{EMOJI_ERROR} Cannot get PID for Tor (Port {port}).{C_RESET}"); return None
    try:
        os.kill(pid_to_signal, signal.SIGHUP)
        print(f"{C_GREEN}{EMOJI_SUCCESS} SIGHUP sent to Tor (Port {port}, PID {pid_to_signal}). Waiting for new IP (5-10s)...{C_RESET}")
        time.sleep(random.randint(5, 10))
        new_ip = get_ip(port, verbose=True)
        if new_ip: print(f"{C_GREEN}{EMOJI_SUCCESS} New IP (Port {port}): {new_ip}{C_RESET}"); return new_ip
        else: print(f"{C_RED}{EMOJI_ERROR} Failed to get new IP (Port {port}) after SIGHUP.{C_RESET}"); return None
    except ProcessLookupError:
        print(f"{C_RED}{EMOJI_ERROR} Tor process (PID {pid_to_signal}, Port {port}) not found (crashed?).{C_RESET}"); return None
    except Exception as e:
        print(f"{C_RED}{EMOJI_ERROR} Failed SIGHUP/get new IP (Port {port}, PID {pid_to_signal}): {e}{C_RESET}"); return None

def cleanup_tor_instances(instances_info_list):
    """
    Terminates managed Tor instances and removes their data directories.
    """
    print_infotainment()
    if not instances_info_list: print(f"{C_BLUE}{EMOJI_INFO} No managed Tor instances to clean up.{C_RESET}"); return
    print(f"{C_BLUE}{EMOJI_WAIT} Cleaning up {len(instances_info_list)} managed Tor instance(s)...{C_RESET}")
    for info in reversed(instances_info_list): # Cleanup in reverse order of creation
        port = info.get("port", "N/A"); process = info.get("process"); data_dir = info.get("data_dir"); log_fp = info.get("log_fp")
        if process and process.poll() is None: # Check if process is running
            print(f"{C_YELLOW}{EMOJI_WAIT} Stopping Tor instance (Port {port}, PID {process.pid})...{C_RESET}")
            try:
                process.terminate(); process.wait(timeout=5)
                print(f"{C_GREEN}{EMOJI_SUCCESS} Tor (Port {port}) terminated gracefully.{C_RESET}")
            except subprocess.TimeoutExpired:
                print(f"{C_YELLOW}{EMOJI_WARNING} Tor (Port {port}) timeout. Killing...{C_RESET}")
                process.kill(); process.wait(timeout=2)
                print(f"{C_GREEN}{EMOJI_SUCCESS} Tor (Port {port}) killed.{C_RESET}")
            except Exception as e:
                print(f"{C_RED}{EMOJI_ERROR} Failed to stop Tor (Port {port}): {e}{C_RESET}")
        if log_fp: 
            try: log_fp.close()
            except Exception: pass
        if data_dir and os.path.exists(data_dir):
            print(f"{C_YELLOW}{EMOJI_WAIT} Removing data_dir '{data_dir}' (Port {port})...{C_RESET}")
            try:
                shutil.rmtree(data_dir)
                print(f"{C_GREEN}{EMOJI_SUCCESS} Removed data_dir for Port {port}.{C_RESET}")
            except Exception as e:
                print(f"{C_RED}{EMOJI_ERROR} Failed to remove data_dir '{data_dir}': {e}{C_RESET}")
    print(f"{C_GREEN}{EMOJI_SUCCESS} Tor instance cleanup complete.{C_RESET}")

# --------------------------------------------------------------------------
# Legacy functions (may need review/removal if fully replaced)
# --------------------------------------------------------------------------

def change_ip_loop(): # System-wide Tor specific
    print(f"{C_YELLOW}{EMOJI_WARNING} 'change_ip_loop' is for system-wide Tor. May not work with dynamic instances.{C_RESET}")
    def original_change_ip_system_tor():
        try:
            print(f"{C_YELLOW}{EMOJI_RELOAD} Requesting new circuit (reloading SYSTEM Tor via systemctl)...{C_RESET}")
            subprocess.run(["sudo", "systemctl", "reload", "tor"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{C_GREEN}{EMOJI_SUCCESS} Tor reload signal sent.{C_RESET}")
            print(f"{C_BLUE}{EMOJI_WAIT} Waiting for new IP (5s)...{C_RESET}"); time.sleep(5)
            new_ip = get_ip(DEFAULT_TOR_PORT, verbose=True)
            if new_ip: show_ip_location(new_ip)
        except Exception as e: print(f"{C_RED}{EMOJI_ERROR} Failed system Tor reload: {e}{C_RESET}")
    try:
        while True: original_change_ip_system_tor(); print(f"{C_BLUE}{EMOJI_INFO} IP change in 60s. Ctrl+C to stop.{C_RESET}"); time.sleep(60)
    except KeyboardInterrupt: print(f"{C_GREEN}{EMOJI_SUCCESS} IP loop stopped.{C_RESET}")

def rotate_ip_and_show_location(instance_info_or_system_port=None):
    new_ip = None
    if isinstance(instance_info_or_system_port, dict):
        new_ip = change_ip(instance_info_or_system_port)
    elif isinstance(instance_info_or_system_port, int) or instance_info_or_system_port is None:
        port = instance_info_or_system_port if isinstance(instance_info_or_system_port, int) else DEFAULT_TOR_PORT
        print(f"{C_YELLOW}{EMOJI_INFO} Rotating IP for system Tor (Port {port})...{C_RESET}")
        try:
            subprocess.run(["sudo", "systemctl", "reload", "tor"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{C_GREEN}{EMOJI_SUCCESS} System Tor reload signal sent. Waiting for new IP (Port {port}, 5-10s)...{C_RESET}"); time.sleep(random.randint(5,10))
            new_ip = get_ip(port, verbose=True)
            if new_ip: print(f"{C_GREEN}{EMOJI_SUCCESS} New system IP (Port {port}): {new_ip}{C_RESET}"); show_ip_location(new_ip)
            else: print(f"{C_RED}{EMOJI_ERROR} Failed to get new system IP (Port {port}).{C_RESET}")
        except Exception as e: print(f"{C_RED}{EMOJI_ERROR} Error rotating system Tor IP (Port {port}): {e}{C_RESET}")
    else: print(f"{C_RED}{EMOJI_ERROR} Invalid arg to rotate_ip_and_show_location.{C_RESET}")

# --- Main execution block for direct testing of pytor.py --- 
if __name__ == "__main__":
    print(f"{C_BLUE}--- pytor.py direct execution test ---{C_RESET}")
    ensure_tor_binary()
    print(f"{C_YELLOW}Testing Port Detection (9050-9052, verbose scan)...{C_RESET}")
    active_system_ports = detect_tor_ports(9050, 9052, verbose_scan=True)
    print(f"Active system ports found: {active_system_ports}")

    print(f"{C_YELLOW}Testing Free Port Finder (need 2, start 9150)...{C_RESET}")
    free_ports_for_test = find_free_ports(2, start_search_port=9150)
    if not free_ports_for_test or len(free_ports_for_test) < 2:
        print(f"{C_RED}Could not find 2 free ports for testing. Aborting further tests.{C_RESET}"); sys.exit(1)
    
    managed_instances = []
    print(f"{C_YELLOW}Testing Tor Instance Creation & Verification (on ports: {free_ports_for_test})...{C_RESET}")
    for i, port_num in enumerate(free_ports_for_test):
        print(f"--- Attempting to start Test Instance #{i+1} on Port {port_num} ---")
        instance = start_tor_instance(port_num)
        if instance and verify_tor_instance(instance, timeout=100): # Generous timeout for CI/slow systems
            managed_instances.append(instance)
            print(f"{C_GREEN}{EMOJI_SUCCESS} Test Instance on port {port_num} is UP.{C_RESET}")
            print(f"{C_YELLOW}Testing IP Rotation for instance on port {port_num}...{C_RESET}")
            ip_before = get_ip(instance["port"], verbose=False)
            print(f"IP before SIGHUP (Port {port_num}): {ip_before if ip_before else 'Failed to get'}")
            new_ip_instance = change_ip(instance)
            print(f"IP after SIGHUP (Port {port_num}): {new_ip_instance if new_ip_instance else 'Failed or no change'}")
            if new_ip_instance and ip_before != new_ip_instance: print(f"{C_GREEN}{EMOJI_SUCCESS} IP change confirmed for Port {port_num}!{C_RESET}")
            elif new_ip_instance: print(f"{C_YELLOW}{EMOJI_WARNING} IP same after SIGHUP (Port {port_num}). Common if circuit reselection is fast.{C_RESET}")
            else: print(f"{C_RED}{EMOJI_ERROR} IP change failed for Port {port_num}.{C_RESET}")
        elif instance: # Started but failed verification
            print(f"{C_RED}{EMOJI_ERROR} Failed to verify instance on port {port_num}. Cleaning it up.{C_RESET}")
            cleanup_tor_instances([instance]) # Clean up only the failed instance
        else: # Failed to start at all
            print(f"{C_RED}{EMOJI_ERROR} Failed to start instance on port {port_num}.{C_RESET}")
    
    if not managed_instances: print(f"{C_RED}{EMOJI_ERROR} No test Tor instances were successfully started. Cleanup test skipped for managed instances.{C_RESET}")
    print(f"{C_YELLOW}Testing Cleanup for {len(managed_instances)} active test instance(s)...{C_RESET}")
    cleanup_tor_instances(managed_instances)
    print(f"{C_BLUE}--- pytor.py direct execution test finished ---{C_RESET}")

# Deprecated/Legacy code that might be removed or heavily refactored:
# install_dependencies() - main.py should handle initial setup
# check_dependencies() - main.py should handle initial setup
# The old change_ip() that only reloads system tor might be removed if main logic uses instance-based change_ip.
