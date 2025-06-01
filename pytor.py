import os
import sys
import time
import subprocess
import random
import re
import socket
import requests

# --------------------------------------------------------------------------
# Tor and IP Management Utilities
# This file contains functions for managing Tor connections,
# checking and installing dependencies, changing IP addresses,
# and fetching IP location information.
# --------------------------------------------------------------------------

def install_dependencies():
    """
    Installs Tor and curl based on the Linux distribution.
    This function is typically called by check_dependencies if they are missing.
    It includes specific commands for Debian/Ubuntu, Fedora/CentOS/Red Hat, and Arch Linux.
    If the distribution is unsupported, it prints an error and exits.
    """
    try:
        distro = subprocess.check_output("lsb_release -d", shell=True).decode().strip()
        if "Ubuntu" in distro or "Debian" in distro:
            print("\033[33mUpdating package lists and installing curl and tor for Debian/Ubuntu...\033[0m")
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "curl", "tor"], check=True)
        elif "Fedora" in distro or "CentOS" in distro or "Red Hat" in distro:
            print("\033[33mInstalling curl and tor for Fedora/CentOS/RHEL...\033[0m")
            subprocess.run(["yum", "install", "-y", "curl", "tor"], check=True)
        elif "Arch" in distro:
            print("\033[33mInstalling curl and tor for Arch Linux...\033[0m")
            subprocess.run(["pacman", "-S", "--noconfirm", "curl", "tor"], check=True)
        else:
            print("\033[1;31mERROR:\033[0m Unsupported distribution!")
            print("\033[1;33m***************************************")
            print("* Supported distributions:            *")
            print("***************************************")
            print("• Ubuntu")
            print("• Debian")
            print("• Fedora")
            print("• CentOS")
            print("• Red Hat")
            print("• Arch")
            print("***************************************\033[0m")
            sys.exit(1)
        print("\033[1;32m✅ Dependencies (curl, tor) installed successfully.\033[0m")
    except Exception as e:
        print(f"\033[1;31mERROR:\033[0m Failed installing dependencies: {e}")
        sys.exit(1)


def check_dependencies():
    """
    Checks if curl and Tor are installed on the system.
    If they are not found, it calls install_dependencies() to install them.
    Uses subprocess.check_call to verify their presence.
    """
    try:
        # Check for curl
        subprocess.check_call(["curl", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Check for Tor
        subprocess.check_call(["tor", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("\033[1;32m✅ Dependencies (curl, tor) are installed.\033[0m")
    except subprocess.CalledProcessError:
        print("\033[33m⚠️ curl and/or tor not found. Attempting to install...\033[0m")
        install_dependencies()
    except FileNotFoundError: # Handles cases where the command itself isn't found
        print("\033[33m⚠️ curl and/or tor not found (FileNotFound). Attempting to install...\033[0m")
        install_dependencies()


def start_tor():
    """
    Starts the Tor service using various system-specific methods.
    It tries systemctl, service, rc-service, and direct pgrep/tor execution.
    Provides feedback on the status of Tor service activation.
    If all automated methods fail, it attempts a manual start and advises the user.
    """
    # Define colors for better UI
    green = "\033[1;32m"
    yellow = "\033[1;33m"
    red = "\033[1;31m"
    blue = "\033[1;34m"
    reset = "\033[0m"
    # Emojis for better visual cues (using standard emoji characters)
    EMOJI_SUCCESS = "✅"
    EMOJI_WARNING = "⚠️"
    EMOJI_ERROR = "❌"
    EMOJI_INFO = "ℹ️"
    EMOJI_WAIT = "⏳"
    EMOJI_DETECT = "🔎"
    EMOJI_START_UP = "🚀"
    EMOJI_CHECK = "✔️" # For already running checks
    
    print(f"{yellow}{EMOJI_WAIT} Attempting to start Tor service...{reset}")
    
    methods = [
        {"check": ["systemctl", "is-active", "--quiet", "tor"], "start": ["systemctl", "start", "tor"], "name": "systemctl"},
        {"check": ["service", "tor", "status"], "start": ["service", "tor", "start"], "name": "service"},
        {"check": ["rc-service", "tor", "status"], "start": ["rc-service", "tor", "start"], "name": "rc-service"},
        {"check": ["pgrep", "tor"], "start": ["tor", "&"], "name": "direct pgrep/tor"} # '&' might be problematic with subprocess.run
    ]
    
    # Check if Tor is already running via pgrep first, as it's often reliable
    try:
        pgrep_check = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if pgrep_check.returncode == 0 and pgrep_check.stdout.strip():
            print(f"{green}{EMOJI_CHECK} Tor service appears to be already running (detected by pgrep).{reset}")
            return
    except FileNotFoundError:
        print(f"{yellow}{EMOJI_WARNING} pgrep command not found. Unable to perform initial check for running Tor.{reset}")

    for method in methods:
        try:
            print(f"{blue}{EMOJI_DETECT} Checking Tor status using '{method['name']}'...{reset}")
            if method["name"] == "direct pgrep/tor": 
                 check_result = subprocess.run(method["check"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                 check_result = subprocess.run(method["check"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if check_result.returncode == 0:
                if method["name"] == "direct pgrep/tor" and not check_result.stdout.strip():
                    pass 
                else:
                    print(f"{green}{EMOJI_CHECK} Tor service is already running (detected via {method['name']}).{reset}")
                    return

            print(f"{blue}{EMOJI_START_UP} Attempting to start Tor using '{method['name']}' (command: {' '.join(method['start'])})...{reset}")
            if method["name"] == "direct pgrep/tor": 
                subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                start_result_code = 0 
            else:
                start_result = subprocess.run(method["start"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                start_result_code = start_result.returncode

            if start_result_code == 0:
                print(f"{yellow}{EMOJI_WAIT} Waiting a few moments for Tor to initialize after starting with '{method['name']}'...{reset}")
                time.sleep(10) 
                
                verify_check = subprocess.run(["pgrep", "-x", "tor"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if verify_check.returncode == 0 and verify_check.stdout.strip():
                    print(f"{green}{EMOJI_SUCCESS} Tor service started successfully using '{method['name']}'!{reset}")
                    return
                else:
                    output_details = f"Output: {start_result.stdout.decode(errors='ignore').strip()} {start_result.stderr.decode(errors='ignore').strip()}".strip()
                    print(f"{yellow}{EMOJI_WARNING} Tor was asked to start with '{method['name']}', but pgrep verification failed. {output_details}{reset}")
            else:
                output_details = f"Output: {start_result.stdout.decode(errors='ignore').strip()} {start_result.stderr.decode(errors='ignore').strip()}".strip()
                print(f"{red}{EMOJI_ERROR} Failed to start Tor with '{method['name']}'. {output_details}{reset}")
                
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"{yellow}{EMOJI_WARNING} Method '{method['name']}' failed or command not found: {e}{reset}")
            continue 
    
    print(f"{red}{EMOJI_ERROR} CRITICAL: All automated methods to start Tor service failed.{reset}")
    print(f"{yellow}{EMOJI_INFO} Please ensure Tor is installed correctly and try starting it manually (e.g., 'sudo service tor start' or 'sudo systemctl start tor').{reset}")


def get_ip(tor_port=9050):
    """
    Fetches the current external IP address through the Tor SOCKS proxy.
    Tries multiple IP checking services (checkip.amazonaws.com, api.ipify.org, icanhazip.com).
    Args:
        tor_port (int): The SOCKS port Tor is listening on. Defaults to 9050.
    Returns:
        str: The external IP address, or exits if all services fail.
    """
    # Emojis (re-using from start_tor or could be defined globally if preferred)
    EMOJI_SUCCESS = "✅"
    EMOJI_WARNING = "⚠️"
    EMOJI_ERROR = "❌"
    EMOJI_INFO = "ℹ️"
    EMOJI_WAIT = "⏳"
    EMOJI_NETWORK = "🌐"

    primary_url = "https://checkip.amazonaws.com"
    secondary_url = "https://api.ipify.org"
    tertiary_url = "https://icanhazip.com"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"} # Common user agent
    proxies = {
        "http": f"socks5h://127.0.0.1:{tor_port}", 
        "https": f"socks5h://127.0.0.1:{tor_port}"
    }
    timeout_seconds = 10

    urls_to_try = [primary_url, secondary_url, tertiary_url]
    
    for i, url in enumerate(urls_to_try):
        try:
            print(f"\033[1;34m{EMOJI_WAIT} Fetching IP via Tor (Port: {tor_port}, Service: {url})...\033[0m")
            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout_seconds)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            ip_address = response.text.strip()
            if not re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip_address): # Basic IP format validation
                raise ValueError("Invalid IP address format received.")
            print(f"\033[1;32m{EMOJI_SUCCESS} Current IP via Tor (Port: {tor_port}):\033[0m {ip_address} ({EMOJI_NETWORK} {url})")
            return ip_address
        except requests.exceptions.RequestException as e:
            print(f"\033[1;31m{EMOJI_ERROR} Service {url} failed: {e}\033[0m")
            if i < len(urls_to_try) - 1:
                print(f"\033[1;33m{EMOJI_WARNING} Switching to next IP service...\033[0m")
        except ValueError as e:
            print(f"\033[1;31m{EMOJI_ERROR} Service {url} returned invalid data: {e}\033[0m")
            if i < len(urls_to_try) - 1:
                print(f"\033[1;33m{EMOJI_WARNING} Switching to next IP service...\033[0m")
    
    print(f"\033[1;31m{EMOJI_ERROR} CRITICAL ERROR: All IP fetching services failed for Tor port {tor_port}. Unable to get current IP.\033[0m")
    sys.exit(1)
        

def change_ip():
    """
    Changes the Tor IP address by reloading the Tor service.
    This function assumes a system-wide Tor service managed by systemctl.
    It waits for a few seconds for the new circuit to establish and then displays the new IP.
    """
    EMOJI_SUCCESS = "✅"
    EMOJI_WARNING = "⚠️"
    EMOJI_ERROR = "❌"
    EMOJI_INFO = "ℹ️"
    EMOJI_WAIT = "⏳"
    EMOJI_RELOAD = "🔄"

    try:
        print(f"\n\033[1;33m{EMOJI_RELOAD} Requesting new Tor circuit (reloading Tor service via systemctl)...\033[0m")
        # Ensure Tor is running before trying to reload
        # We might need a more robust check here or rely on start_tor() being called prior.
        subprocess.run(["systemctl", "reload", "tor"], check=True)
        print(f"\033[1;32m{EMOJI_SUCCESS} Tor reload signal sent successfully.\033[0m")
        print(f"\033[1;34m{EMOJI_WAIT} Waiting for new IP address to activate (5 seconds)...\033[0m")
        time.sleep(5) # Wait for Tor to establish a new circuit
        
        new_ip = get_ip() # Uses the default port 9050 for the system Tor service
        if new_ip:
            show_ip_location(new_ip) # Call show_ip_location if new IP was obtained

    except subprocess.CalledProcessError as e:
        print(f"\033[1;31m{EMOJI_ERROR} Failed reloading Tor service (systemctl reload tor): {e}\033[0m")
        print(f"\033[1;33m{EMOJI_INFO} Ensure Tor is running and systemctl is available. This method is for systemd-based Linux.{EMOJI_WARNING}\033[0m")
    except FileNotFoundError:
        print(f"\033[1;31m{EMOJI_ERROR} systemctl command not found. Cannot reload Tor using this method.{EMOJI_WARNING}\033[0m")


def show_ip_location(ip_address):
    """
    Fetches and displays geolocation information for a given IP address.
    Tries multiple geolocation API services (ipapi.co, ip-api.com, ipwhois.app).
    Args:
        ip_address (str): The IP address to geolocate.
    """
    EMOJI_SUCCESS = "✅"
    EMOJI_WARNING = "⚠️"
    EMOJI_ERROR = "❌"
    EMOJI_INFO = "ℹ️"
    EMOJI_LOCATION_PIN = "📍"
    EMOJI_GLOBE = "🌍"

    if not ip_address:
        print(f"\033[1;31m{EMOJI_ERROR} No IP address provided to geolocate.\033[0m")
        return

    print(f"\033[1;34m{EMOJI_GLOBE} Fetching geolocation for IP: {ip_address}...\033[0m")
    api_services = [
        (f"https://ipapi.co/{ip_address}/json/", ["city", "region", "country_name"], "ipapi.co"),
        (f"http://ip-api.com/json/{ip_address}", ["city", "regionName", "country"], "ip-api.com"),
        (f"https://ipwhois.app/json/{ip_address}", ["city", "region", "country"], "ipwhois.app"),
    ]
    
    random.shuffle(api_services) # Randomize to distribute load and avoid rate limits

    for url, fields, service_name in api_services:
        try:
            response = requests.get(url, timeout=random.randint(8, 15)) # Randomized timeout
            response.raise_for_status()
            data = response.json()
            
            city = data.get(fields[0], 'N/A')
            region = data.get(fields[1], 'N/A')
            country = data.get(fields[2], 'N/A')

            print(f"\033[1;32m{EMOJI_LOCATION_PIN} Location details from {service_name} ({EMOJI_SUCCESS}):\033[0m")
            print(f"  {EMOJI_INFO} City: \033[96m{city}\033[0m")
            print(f"  {EMOJI_INFO} Region: \033[96m{region}\033[0m")
            print(f"  {EMOJI_INFO} Country: \033[96m{country}\033[0m")
            return # Success, no need to try other services
        except requests.exceptions.RequestException as e:
            print(f"\033[1;31m{EMOJI_ERROR} Geolocation service {service_name} ({url}) failed: {e}\033[0m")
        except ValueError: # Handles JSON decoding errors
            print(f"\033[1;31m{EMOJI_ERROR} Geolocation service {service_name} ({url}) returned invalid JSON.{EMOJI_WARNING}\033[0m")
            
    print(f"\033[1;31m{EMOJI_ERROR} All geolocation services failed for IP {ip_address}.{EMOJI_WARNING}\033[0m")
    

def change_ip_loop():
    """
    Interactive loop to repeatedly change Tor IP at user-defined intervals and counts.
    This is a utility function for users who want to cycle their system Tor IP.
    """
    try:
        print("\n\033[1;35m--- IP Address Cycler (System Tor) ---")
        while True:
            interval_str = input("\033[1;36mEnter time interval in seconds (e.g., 60, or 0 for random 10-20s default): \033[0m").strip()
            times_str = input("\033[1;36mEnter how many times to change IP (e.g., 5, or 0 for infinite): \033[0m").strip()
            print("\n\033[1;35mPress CTRL + C to quit this loop at any time.\033[0m")
            
            if not interval_str.isdigit() or not times_str.isdigit():
                print("\n\033[1;31mERROR:\033[0m Please enter valid numbers for interval and count.")
                continue

            interval = int(interval_str)
            times_to_change = int(times_str)
            
            is_infinite_changes = (times_to_change == 0)
            is_random_interval = (interval == 0)

            if is_infinite_changes:
                print("\n\033[33m🚀 Starting infinite IP changes...\033[0m")
            else:
                print(f"\n\033[33m🚀 Starting IP changes ({times_to_change} times)...\033[0m")

            current_change_count = 0
            while is_infinite_changes or current_change_count < times_to_change:
                if not is_infinite_changes:
                    print(f"\n--- Change {current_change_count + 1} of {times_to_change} ---")
                else:
                    print(f"\n--- Change {current_change_count + 1} ---")

                change_ip() # This will attempt to change IP and show location

                current_change_count += 1
                if not is_infinite_changes and current_change_count >= times_to_change:
                    break # Exit loop if count reached

                sleep_duration = random.randint(10, 20) if is_random_interval else interval
                if sleep_duration <=0 : # Ensure positive sleep
                    sleep_duration = random.randint(10,20)
                    print(f"\033[1;33m⚠️ Invalid interval, using random {sleep_duration}s sleep.\033[0m")
                else:
                     print(f"\033[1;34m⏳ Sleeping for {sleep_duration} seconds...\033[0m")
                time.sleep(sleep_duration)
            
            print("\033[1;32m✅ IP changing loop finished.\033[0m")
            break # Exit the outer while True loop after finishing a cycle

    except KeyboardInterrupt:
        print("\n\033[1;33m⏹️ IP Cycler interrupted by user. Exiting IP loop...\033[0m")
    except Exception as e:
        print(f"\n\033[1;31mERROR in IP Cycler: {e}\033[0m")


def rotate_ip_and_show_location():
    """
    A utility function that combines changing the Tor IP and showing its new location.
    This is primarily for the system-wide Tor instance.
    """
    print("\n\033[1;35m--- Rotating System Tor IP and Showing Location ---")
    # This function implicitly uses the system 'tor' service and its default port for get_ip
    ip = change_ip()
    if ip:
        show_ip_location(ip)


if __name__ == '__main__':
    # Example usage for testing pytor.py functions directly
    print("\033[1;35mTesting PyTor Utilities...\033[0m")
    
    # This requires root/admin for install_dependencies and start_tor if not already running/installed
    # On Linux, ensure you run 'sudo python pytor.py' if testing these.
    
    # print("\n--- Checking Dependencies ---")
    # check_dependencies() # Checks and installs Tor/curl if needed

    # print("\n--- Starting Tor Service ---")
    # start_tor() # Ensures Tor service is running
    
    print("\n--- Getting Initial IP (Port 9050) ---")
    initial_ip = get_ip(tor_port=9050)
    if initial_ip:
        show_ip_location(initial_ip)

    # print("\n--- Rotating IP and Showing Location ---")
    # rotate_ip_and_show_location() # Changes IP and shows new location

    # print("\n--- Interactive IP Change Loop ---")
    # print("You can test the interactive IP changer now.")
    # change_ip_loop()
    
    print("\n\033[1;32mPyTor Utilities testing done.\033[0m")
