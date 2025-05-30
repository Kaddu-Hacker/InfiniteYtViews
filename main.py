#!/usr/bin/env python3
import os
import sys
import time
import random
import subprocess
import requests
from urllib.parse import urlparse
import threading
import signal
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import PyTor functions
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "PyTor-IP-Changer-main"))
from pytor import check_dependencies, start_tor, change_ip, get_ip, rotate_ip_and_show_location

# Import the refactored pytor.py
import pytor

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

BANNER = f"""
{Colors.HEADER}{EMOJIS['kaddu']} {Colors.BOLD}KADDU YT-VIEWS SYSTEM {EMOJIS['views']}{Colors.ENDC}
{Colors.OKCYAN}Automated, Smart, and Human-like View Simulation!{Colors.ENDC}
{Colors.GRAY}{EMOJIS['rocket']} Powered by PyTor Tech {EMOJIS['rocket']}{Colors.ENDC}
{Colors.GRAY}{'-'*55}{Colors.ENDC}
{Colors.OKBLUE}GitHub: https://github.com/Kaddu-Hacker/InfiniteYtViews{Colors.ENDC}
"""

HELP_TEXT = f"""
{Colors.OKCYAN}{EMOJIS['info']} HELP MENU {EMOJIS['info']}{Colors.ENDC}
- This tool simulates views for your YouTube videos and shorts.
- Add multiple links when prompted.
- {Colors.BOLD}Default settings are recommended for most users.{Colors.ENDC}
- If you see [Press Enter for recommended], just press Enter!
- {Colors.WARNING}'Dry run'{Colors.ENDC} mode previews actions without actual views.
- For best results, avoid other Tor activities during operation.
- Each 'connection' uses a distinct Tor circuit for better diversity.
"""

TIP_TEXT = f"{Colors.OKBLUE}{EMOJIS['tip']} TIP: Use default settings and let the tool work for optimal results!{Colors.ENDC}"

NEXT_TEXT = f"""
{Colors.OKGREEN}{EMOJIS['next']} WHAT'S NEXT?
- Check video analytics after some time for view updates.
- Run this tool again for more views.
- Share your experience and the tool with friends!
"""

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
    """
    print(f"\n{Colors.HEADER}{EMOJIS['star']} System Setup {EMOJIS['star']}{Colors.ENDC}")
    try:
        requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        if not os.path.exists(requirements_file):
            print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] requirements.txt not found! Please create it.{Colors.ENDC}")
            # Attempt to create a basic one if it's missing, though it might not be complete.
            print(f"{Colors.WARNING}{EMOJIS['info']} Attempting to create a basic requirements.txt...{Colors.ENDC}")
            with open(requirements_file, 'w') as f:
                f.write("requests\n") # Add other known essential deps if any
                f.write("PySocks\n") # For SOCKS proxy support with requests if Tor needs it explicitly
            print(f"{Colors.OKGREEN}{EMOJIS['success']} Basic requirements.txt created. Please verify its contents.{Colors.ENDC}")

        print(f"{Colors.OKBLUE}{EMOJIS['wait']} Installing/updating Python packages from {requirements_file}...{Colors.ENDC}")
        # Ensure pip is up to date
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print(f"{Colors.OKGREEN}{EMOJIS['success']} Python packages installed/updated successfully.{Colors.ENDC}")

    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] Failed to install Python packages: {e}{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] An unexpected error occurred during package installation: {e}{Colors.ENDC}")
        sys.exit(1)

    print(f"\n{Colors.OKBLUE}{EMOJIS['wait']} Checking and ensuring Tor service...{Colors.ENDC}")
    try:
        pytor.check_dependencies() # Installs Tor if not present
        pytor.start_tor()        # Starts Tor service
        print(f"{Colors.OKGREEN}{EMOJIS['success']} Tor setup checks completed.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}{EMOJIS['error']} [ERROR] Failed during Tor setup: {e}{Colors.ENDC}")
        print(f"{Colors.WARNING}Please ensure Tor can be installed and started. You might need to run 'sudo apt-get install tor' or similar manually, then restart the script.{Colors.ENDC}")
        # Consider not exiting, to allow users to fix Tor manually and retry, or if Tor is optional for some parts.
        # sys.exit(1) 

def get_user_links():
    """
    Prompts the user for link details (URL, type, length).
    Returns a list of link dictionaries.
    """
    print(f"\n{Colors.HEADER}{EMOJIS['link']} Let's add your videos/shorts! {EMOJIS['link']}{Colors.ENDC}")
    links = []
    while True:
        try:
            num_links_str = input(f"{Colors.OKCYAN}{EMOJIS['prompt']} How many videos/shorts? (Enter a number, or 'help'): {Colors.ENDC}").strip()
            if num_links_str.lower() == 'help':
                print(HELP_TEXT)
                continue
            num_links = int(num_links_str) if num_links_str else 1
            if num_links < 1:
                print(f"{Colors.WARNING}{EMOJIS['error']} Please enter a positive number.{Colors.ENDC}")
                continue
            break
        except ValueError:
            print(f"{Colors.WARNING}{EMOJIS['error']} Invalid input. Please enter a number.{Colors.ENDC}")

    for i in range(num_links):
        print(f"\n{Colors.OKBLUE}--- Link #{i+1} ---{Colors.ENDC}")
        while True:
            link_url = input(f"  {EMOJIS['prompt']} Enter URL for link #{i+1}: ").strip()
            if link_url.lower() == 'help':
                print(HELP_TEXT)
                continue
            if not link_url:
                 print(f"{Colors.WARNING}{EMOJIS['error']} URL cannot be empty.{Colors.ENDC}")
                 continue
            if not (link_url.startswith("http://") or link_url.startswith("https://")):
                print(f"{Colors.WARNING}{EMOJIS['error']} Invalid URL format. Must start with http:// or https://{Colors.ENDC}")
                continue
            break
        
        while True:
            vtype_str = input(f"  {EMOJIS['prompt']} Is this a Video or a Short? (v/s) [Press Enter for Video]: ").strip().lower()
            if vtype_str == 'help':
                print(HELP_TEXT)
                continue
            vtype = vtype_str if vtype_str in ['v', 's'] else 'v'
            break
        
        link_type = 'video' if vtype == 'v' else 'short'
        default_length = 60 if link_type == 'short' else 300
        min_length = 10 if link_type == 'short' else 60
        length_prompt = f"  {EMOJIS['prompt']} Enter {link_type} length in seconds [Press Enter for {default_length}s]: "

        while True:
            length_str = input(length_prompt).strip()
            if length_str.lower() == 'help':
                print(HELP_TEXT)
                continue
            try:
                length_sec = int(length_str) if length_str else default_length
                if length_sec < min_length:
                    print(f"{Colors.WARNING}{EMOJIS['error']} Minimum length for a {link_type} is {min_length}s. Please enter a realistic length.{Colors.ENDC}")
                    continue
                break
            except ValueError:
                print(f"{Colors.WARNING}{EMOJIS['error']} Invalid input. Please enter a number for length.{Colors.ENDC}")
        links.append({'url': link_url, 'type': link_type, 'length': length_sec, 'id': i})
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
    # On Windows systems
    elif os.name == 'nt':
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("\033[1;31mERROR:\033[0m This script must be run as administrator.")
            print("Please right-click on Command Prompt or PowerShell and select 'Run as administrator'")
            sys.exit(1)

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
    print(f"\n{Colors.OKBLUE}{EMOJIS['info']} Checking Tor Connection Status(es)...{Colors.ENDC}")
    any_successful = False
    for i in range(num_connections):
        port = base_tor_port + i
        print(f"{Colors.GRAY}  Attempting to get IP for Tor SOCKS port {port}...{Colors.ENDC}")
        try:
            # Assuming pytor.get_ip is robust and handles its own retries/timeouts for a single port check
            current_ip = pytor.get_ip(tor_port=port) 
            if current_ip: # pytor.get_ip returns IP string on success, or handles its own error printing and exits on total failure
                print(f"{Colors.OKGREEN}{EMOJIS['success']} Connection via Port {port}: External IP {current_ip}{Colors.ENDC}")
                any_successful = True
            else:
                # This case might not be hit if pytor.get_ip exits on failure for that port.
                print(f"{Colors.FAIL}{EMOJIS['error']} Could not get IP for Port {port}. Ensure Tor is active and configured for this SOCKS port.{Colors.ENDC}")
        except Exception as e:
            # Catch any other unexpected exceptions during the IP check for a specific port
            print(f"{Colors.FAIL}{EMOJIS['error']} Error while checking Tor Port {port}: {e}{Colors.ENDC}")
    if not any_successful and num_connections > 0:
        print(f"{Colors.WARNING}{EMOJIS['error']} Failed to confirm external IP for any Tor SOCKS port. \
                  Please check your Tor configuration and ensure it's running and accessible on the configured ports (starting from {base_tor_port}).{Colors.ENDC}")

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
    os.system('') # For colors in Windows CMD
    print(BANNER)
    
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
        short_url = url[:40] + '...' if len(url) > 43 else url
        # Print immediate feedback for each view attempt
        print(f"\r{status_color}{status_emoji} Link ID {link_id} ({short_url}): View #{views_done_link} ({total_done_overall} total) via Port {port} ({watch_time}s). {Colors.ENDC}          ")

        # Print a summary less frequently to avoid too much scroll
        # Adjust frequency based on number of links/connections to be reasonable
        print_summary_interval = len(validated_links) * max(1, num_parallel_connections // 2)
        if print_summary_interval == 0: print_summary_interval = 1 # Avoid division by zero if no links/connections (though unlikely here)
        
        if total_done_overall % print_summary_interval == 0 or total_done_overall == 1:
            elapsed_time = time.time() - start_time_proc
            avg_time_per_view = elapsed_time / total_done_overall if total_done_overall > 0 else 0
            views_remaining_str = "Continuous" 
            if views_per_target_link > 0:
                total_target_views = len(validated_links) * views_per_target_link
                views_remaining = total_target_views - total_done_overall
                views_remaining_str = str(max(0, views_remaining)) # Ensure non-negative
            # Ensure a newline before this summary if many rapid view updates happened
            print(f"\n{Colors.OKCYAN}{EMOJIS['progress']} Overall: {total_done_overall} views. Target Remaining: {views_remaining_str}. Avg time/view: {avg_time_per_view:.2f}s.{Colors.ENDC}")
    
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