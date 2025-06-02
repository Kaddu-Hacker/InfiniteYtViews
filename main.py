#!/usr/bin/env python3
# --- MINIMAL IMPORTS FOR SETUP CHECKS ---
import os
import sys
import subprocess
import shutil
import importlib.util
import time
import threading
import platform
import urllib.request
import zipfile
import tarfile
from urllib.parse import urlparse
import concurrent.futures
import itertools
import random
import re

# --- SELENIUM IMPORTS ---
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
# from selenium.webdriver.chrome.options import Options as ChromeOptions # Example for Chrome
# from selenium.webdriver.chrome.service import Service as ChromeService # Example for Chrome
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- OTHER STANDARD IMPORTS ---
# import itertools # Moved up
# import random # Moved up

# --- PYTOR IMPORT ---
# Attempt to import the local pytor.py module
try:
    import pytor
    # print(f"{C_GREEN}Successfully imported pytor module.{C_END}") # Optional: for debugging initial setup
except ImportError:
    print(f"{C_WARNING}{EMOJI_WARNING} pytor.py module not found. IP changing and advanced Tor management will be limited.{C_END}")
    pytor = None # Define pytor as None so checks like 'if pytor:' don't raise NameError
except Exception as e:
    print(f"{C_FAIL}{EMOJI_ERROR} Error importing pytor: {e}. IP changing may be affected.{C_END}")
    pytor = None

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
EMOJI_VIDEO = "📹"
EMOJI_SHORT = "⏱️"
EMOJI_LINK = "🔗"
EMOJI_THREADS = "🧵"
EMOJI_WAIT = "⏳"

C_HEADER = '\033[95m'
C_BLUE = '\033[94m'
C_CYAN = '\033[96m'
C_GREEN = '\033[92m'
C_WARNING = '\033[93m'
C_FAIL = '\033[91m'
C_END = '\033[0m'
C_BOLD = '\033[1m'
C_GRAY = '\033[90m'
C_UNDERLINE = '\033[4m'
C_YELLOW = '\033[93m'
C_WHITE = '\033[97m'
C_OKBLUE = C_BLUE
C_OKGREEN = C_GREEN

# --- HELP TEXT (IMPROVED) ---
HELP_TEXT = f""" 
KADDU YT-VIEWS Help & Troubleshooting

Usage:
  - Run this script with: python3 main.py
  - Follow the prompts to enter YouTube links, number of views, and connections.
  - Type 'help' at any prompt to see this message.

Troubleshooting:
  - Ensure you are in a Python virtual environment (venv).
  - The script will attempt to install all dependencies automatically.
  - If Tor or geckodriver cannot be installed automatically, the script will print the download URL and instructions.
  - If you see a permissions error, try running with: sudo -E python3 main.py
  - For more info, see the README.md or visit: https://github.com/Kaddu-Hacker/InfiniteYtViews

Contact:
  - For issues, open an issue on GitHub or contact the maintainer.
"""

# --- GLOBAL STOP EVENT FOR THREAD CONTROL ---
stop_event_global = threading.Event()

# --- GLOBAL LOCK FOR THREADING ---
completed_views_lock = threading.Lock()

# --- GLOBAL COUNTERS FOR VIEWS ---
overall_completed_views_total = 0
overall_failed_attempts_total = 0

# --- USER AGENT LIST (Expanded for better non-detectability) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0", # Firefox 109 was a ESR version
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0", # Older ESR Firefox for Linux
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/109.0.5414.74",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    # Consider using a library for more diverse and up-to-date user agents in a production tool.
]

def get_random_user_agent():
    """Selects a random user agent from the list."""
    if not USER_AGENTS: # Fallback in case list is somehow empty
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    return random.choice(USER_AGENTS)

# --- INFOTAINMENT MESSAGES ---
INFOTAINMENT_MESSAGES = [
    "🚀 Fun Fact: The first YouTube video was 'Me at the zoo', uploaded on April 23, 2005.",
    "💡 Tip: A stable internet connection improves view success rates!",
    "🌟 Keep Going: Every simulated view is a step towards your goal!",
    "🤓 Tech Tidbit: Tor stands for 'The Onion Router'.",
    "🎉 Progress: You're making great progress with KADDU YT-VIEWS!",
    "✨ Stay Curious: Explore the world of privacy tech!",
    "🧐 Did You Know: Selenium is a powerful tool for web automation.",
    "⏳ Patience is Key: Good things take time, especially with network anonymization.",
    "💖 Thanks for using KADDU YT-VIEWS! Consider starring the project on GitHub!",
    "🌍 Reminder: Use this tool responsibly and ethically.",
    "🔒 Privacy Tip: Always use a fresh Tor circuit for each session!",
    "🧅 Onion Routing: Your traffic is layered for maximum privacy.",
    "📈 Analytics: YouTube uses advanced detection, so randomness is your friend!",
    "🦾 Automation: This script automates everything for you, just sit back and relax!",
    "🛡️ Security: Never share your Tor identity with anyone.",
    "🎬 Entertainment: Enjoy the ASCII art banner at every launch!",
    "🧠 Knowledge: Learn more about Tor at torproject.org.",
    "🔄 Rotation: Each view uses a new Tor IP for best results.",
    "🧪 Experiment: Try different user agents for more realism.",
    "🦉 Wisdom: The best privacy is the one you control!"
]

def get_random_infotainment():
    return random.choice(INFOTAINMENT_MESSAGES)

# --- Ensure geckodriver is available ---
def ensure_geckodriver_available():
    """
    Ensures geckodriver is available in PATH. If not, downloads and extracts it to ./drivers/ and adds to PATH.
    """
    import shutil
    import stat
    GECKO_URL_BASE = "https://github.com/mozilla/geckodriver/releases/latest/download/"
    drivers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "drivers")
    os.makedirs(drivers_dir, exist_ok=True)
    geckodriver_name = "geckodriver.exe" if os.name == "nt" else "geckodriver"
    gecko_local_path = os.path.join(drivers_dir, geckodriver_name)

    # 1. Check if geckodriver is already in PATH
    if shutil.which("geckodriver"):
        print(f"{C_GREEN}{EMOJI_SUCCESS} geckodriver is already available in PATH.{C_END}")
        return
    # 2. Check if it's in ./drivers/ and add to PATH if found
    if os.path.exists(gecko_local_path):
        # Ensure it's executable if on Unix-like systems
        if os.name != "nt" and not os.access(gecko_local_path, os.X_OK):
            try:
                os.chmod(gecko_local_path, os.stat(gecko_local_path).st_mode | stat.S_IEXEC)
                print(f"{C_GREEN}{EMOJI_INFO} Made geckodriver in ./drivers/ executable.{C_END}")
            except Exception as e:
                print(f"{C_WARNING}{EMOJI_WARNING} Could not set executable permission on geckodriver: {e}{C_END}")
        
        os.environ["PATH"] = drivers_dir + os.pathsep + os.environ["PATH"]
        print(f"{C_GREEN}{EMOJI_SUCCESS} geckodriver found in ./drivers/. Added to PATH for this session.{C_END}")
        if shutil.which("geckodriver"): # Verify it's now findable
             print(f"{C_GREEN}{EMOJI_SUCCESS} geckodriver confirmed in PATH after adding ./drivers/.{C_END}")
        else:
             print(f"{C_WARNING}{EMOJI_WARNING} Added ./drivers/ to PATH, but geckodriver still not found by shutil.which(). Manual check needed.{C_END}")
        return

    # 3. Detect OS and arch for download
    sys_plat = platform.system().lower()
    arch = platform.machine().lower()

    if sys_plat.startswith("win"): # Windows (win32 or win64)
        gecko_asset = "geckodriver-latest-win64.zip" if "64" in arch else "geckodriver-latest-win32.zip"
    elif sys_plat == "darwin": # macOS
        gecko_asset = "geckodriver-latest-macos-aarch64.tar.gz" if arch == "arm64" else "geckodriver-latest-macos.tar.gz"
    elif sys_plat == "linux": # Linux
        if arch in ("x86_64", "amd64"):
            gecko_asset = "geckodriver-latest-linux64.tar.gz"
        elif arch in ("aarch64", "arm64"): # Added arm64 for Linux
            gecko_asset = "geckodriver-latest-linux-aarch64.tar.gz"
        elif arch == "armv7l": # Example for 32-bit ARM
             gecko_asset = "geckodriver-latest-linux-arm7hf.tar.gz" # Note: Check exact filename from Mozilla
        else:
            print(f"{C_FAIL}{EMOJI_ERROR} Unsupported Linux architecture for geckodriver: {arch}{C_END}")
            print(f"{C_CYAN}{EMOJI_INFO} Please download geckodriver manually for your system and place it in the PATH or in the ./drivers/ directory.{C_END}")
            print(f"{C_CYAN}{EMOJI_INFO} Download geckodriver manually from: https://github.com/mozilla/geckodriver/releases/latest{C_END}")
            # Manual install instructions only, no QR code logic
            try:
                import webbrowser
                webbrowser.open("https://github.com/mozilla/geckodriver/releases/latest")
            except Exception:
                pass
            return
    else:
        print(f"{C_FAIL}{EMOJI_ERROR} Unsupported OS for geckodriver: {sys_plat}{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} Please download geckodriver manually for your system and place it in the PATH or in the ./drivers/ directory.{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} Download geckodriver manually from: https://github.com/mozilla/geckodriver/releases/latest{C_END}")
        # Manual install instructions only, no QR code logic
        try:
            import webbrowser
            webbrowser.open("https://github.com/mozilla/geckodriver/releases/latest")
        except Exception:
            pass
        return

    gecko_url = GECKO_URL_BASE + gecko_asset
    print(f"{C_CYAN}{EMOJI_INFO} Downloading geckodriver from: {gecko_url}{C_END}")
    archive_path = os.path.join(drivers_dir, gecko_asset)
    try:
        urllib.request.urlretrieve(gecko_url, archive_path)
    except Exception as e:
        print(f"{C_FAIL}{EMOJI_ERROR} Failed to download geckodriver: {e}{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} Please download geckodriver manually and place it in the PATH or in the ./drivers/ directory.{C_END}")
        return

    # 4. Extract
    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(drivers_dir)
        elif archive_path.endswith(".tar.gz"):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                # Ensure the extracted geckodriver is placed directly in drivers_dir, not a subdirectory
                for member in tar_ref.getmembers():
                    if member.name == geckodriver_name or member.name.endswith('/' + geckodriver_name):
                         member.name = os.path.basename(member.name) # Strip any parent folders from archive
                         tar_ref.extract(member, drivers_dir)
                         break # Found and extracted
                else: # if no break
                    # Fallback if specific extraction failed, try extracting all
                    tar_ref.extractall(drivers_dir)


        else:
            print(f"{C_FAIL}{EMOJI_ERROR} Unknown archive format for geckodriver: {archive_path}{C_END}")
            return
        print(f"{C_GREEN}{EMOJI_SUCCESS} geckodriver extracted to {drivers_dir}{C_END}")
    except Exception as e:
        print(f"{C_FAIL}{EMOJI_ERROR} Failed to extract geckodriver: {e}{C_END}")
        return
    finally:
        try:
            if os.path.exists(archive_path): os.remove(archive_path)
        except Exception:
            pass # Non-critical if removal fails

    # 5. Set permissions (Linux/Mac) and re-check local path
    if not os.path.exists(gecko_local_path):
        print(f"{C_FAIL}{EMOJI_ERROR} geckodriver not found at {gecko_local_path} after extraction. Please check the archive contents or install manually.{C_END}")
        print(f"{C_CYAN}{EMOJI_INFO} Download geckodriver manually from: https://github.com/mozilla/geckodriver/releases/latest{C_END}")
        # Manual install instructions only, no QR code logic
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
            print(f"{C_WARNING}{EMOJI_WARNING} Could not set executable permission on geckodriver at {gecko_local_path}: {e}{C_END}")

    # 6. Add to PATH for this process
    os.environ["PATH"] = drivers_dir + os.pathsep + os.environ["PATH"]
    if shutil.which("geckodriver"):
        print(f"{C_GREEN}{EMOJI_SUCCESS} geckodriver is ready and added to PATH for this session!{C_END}")
    else:
        print(f"{C_WARNING}{EMOJI_WARNING} geckodriver downloaded and extracted to ./drivers/, and ./drivers/ added to PATH, but shutil.which() still cannot find it. Selenium might fail if geckodriver is not discoverable. Ensure {gecko_local_path} is executable and correctly named.{C_END}")


# --- SIMULATE VIEW WITH SELENIUM ---
def simulate_view_with_selenium(video_url, tor_socks_port, watch_duration, link_title="N/A"):
    """
    Simulates viewing a YouTube video using Selenium with Firefox routed through Tor.
    Uses a random user agent and attempts to handle pop-ups and play buttons.
    Enhanced privacy options for non-detectability.
    """
    print(f"{C_CYAN}{EMOJI_VIEW} Attempting to view '{link_title}' ({video_url[:40]}...) via Port {tor_socks_port} for {watch_duration}s using Selenium...{C_END}")
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.set_preference("general.useragent.override", get_random_user_agent())
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", int(tor_socks_port))
    options.set_preference("network.proxy.socks_remote_dns", True)
    options.set_preference("media.volume_scale", "0.0")
    # Enhanced privacy options
    options.set_preference("media.peerconnection.enabled", False)
    options.set_preference("geo.enabled", False)
    options.set_preference("privacy.trackingprotection.enabled", True)
    options.set_preference("privacy.trackingprotection.fingerprinting.enabled", True)
    options.set_preference("privacy.trackingprotection.cryptomining.enabled", True)
    options.set_preference("privacy.donottrackheader.enabled", True)
    options.set_preference("network.cookie.cookieBehavior", 5)
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    # options.set_preference("privacy.resistFingerprinting", True) # Can break sites
    driver = None
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(100)
        print(f"{C_GRAY}  Selenium: Navigating to {video_url} via Tor port {tor_socks_port}...{C_END}")
        driver.get(video_url)
        print(f"{C_GRAY}  Selenium: Waiting for video element or YouTube page title...{C_END}")
        WebDriverWait(driver, 60).until(
             EC.any_of(
                EC.presence_of_element_located((By.TAG_NAME, "video")),
                EC.title_contains("YouTube") 
            )
        )
        print(f"{C_GREEN}  Selenium: Page appears loaded (video or YT title found).{C_END}")
        
        # Attempt to handle cookie consent pop-ups (more robust selectors)
        consent_selectors = [
            "//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree to all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]",
            "//button[@id='L2AGLb']", # Google's specific ID
            "//div[@role='dialog']//button[contains(text(), 'Accept') or contains(text(), 'Agree') or contains(text(), 'Allow') or contains(text(),'OK')]",
            "form[action*='consent.youtube.com'] button",
            "//button[@aria-label='Accept all']"
        ]
        consent_clicked = False
        for i, selector in enumerate(consent_selectors):
            if stop_event_global.is_set(): raise KeyboardInterrupt("Stop signal during consent check")
            try:
                consent_button = WebDriverWait(driver, 5).until( # Shorter timeout for each attempt
                    EC.element_to_be_clickable((By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector))
                )
                print(f"{C_GRAY}  Selenium: Found potential consent button (selector #{i+1}). Clicking...{C_END}")
                # Try JavaScript click first, as it can be more reliable for complex elements
                driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", consent_button)
                print(f"{C_GREEN}  Selenium: Clicked consent button (selector #{i+1}).{C_END}")
                consent_clicked = True
                time.sleep(random.uniform(2, 5)) # Wait for pop-up to disappear/page to react
                break 
            except TimeoutException:
                if i == len(consent_selectors) - 1 and not consent_clicked:
                    print(f"{C_GRAY}  Selenium: No generic consent pop-up button found or needed after all attempts.{C_END}")
            except Exception as e_consent:
                print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Minor error trying to click consent button (Selector #{i+1}): {str(e_consent).splitlines()[0]}{C_END}")
        
        # Attempt to click the main play button on YouTube if video is not auto-playing
        try:
            if stop_event_global.is_set(): raise KeyboardInterrupt("Stop signal before play check")
            video_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            is_paused = driver.execute_script("return arguments[0].paused;", video_element)
            
            if is_paused:
                print(f"{C_GRAY}  Selenium: Video detected as paused. Attempting to click play button...{C_END}")
                play_button_selectors = [
                    "button.ytp-large-play-button.ytp-button",
                    "button[aria-label='Play (k)']",
                    "button[data-title-no-tooltip='Play']",
                    ".html5-main-video" # Clicking the video element itself as a last resort
                ]
                play_button_clicked_success = False
                for pb_selector in play_button_selectors:
                    if stop_event_global.is_set(): raise KeyboardInterrupt("Stop signal during play button check")
                    try:
                        play_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, pb_selector))
                        )
                        if play_button and play_button.is_displayed():
                            # play_button.click() # Standard click
                            driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", play_button) # JS Click
                            print(f"{C_GREEN}  Selenium: Clicked video play button (selector: {pb_selector}).{C_END}")
                            play_button_clicked_success = True
                            time.sleep(random.uniform(1,3)) # Give time for play to start
                            break
                    except Exception:
                        pass 
                if not play_button_clicked_success:
                    print(f"{C_GRAY}  Selenium: Could not find/click a main play button, or video started playing automatically/differently.{C_END}")
            else:
                print(f"{C_GRAY}  Selenium: Video appears to be playing or autoplaying (not explicitly paused).{C_END}")

        except TimeoutException:
            print(f"{C_GRAY}  Selenium: Video element or play button not found/interactable as expected (might be autoplaying or structure changed).{C_END}")
        except KeyboardInterrupt as ki:
            raise ki # Re-raise to be caught by main try-except
        except Exception as e_play:
            print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Minor error interacting with video/play button: {str(e_play)[:100]}{C_END}")

        # Simulate watch time with slight variation and interruption check
        actual_watch_duration = max(5, int(watch_duration + random.uniform(-watch_duration * 0.1, watch_duration * 0.1)))
        
        print(f"{C_GRAY}  Selenium: Simulating watch time for ~{actual_watch_duration} seconds... (Ctrl+C to stop this view){C_END}")
        start_watch_time = time.time()
        while time.time() - start_watch_time < actual_watch_duration:
            if stop_event_global.is_set():
                print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Watch time for '{link_title}' on Port {tor_socks_port} interrupted by global stop signal.{C_END}")
                # if driver: driver.save_screenshot(f"interrupt_watch_{link_title[:10]}_{tor_socks_port}.png")
                return False, "Watch interrupted by stop signal"
            time.sleep(1) 
            
        print(f"{C_GREEN}{EMOJI_SUCCESS} Selenium: Successfully simulated view for '{link_title}' for {actual_watch_duration}s.{C_END}")
        # if driver: driver.save_screenshot(f"success_{link_title[:10]}_{tor_socks_port}.png")
        return True, f"Watched for {actual_watch_duration}s"
    
    except KeyboardInterrupt: # Catch Ctrl+C specifically during Selenium ops
        print(f"\\n{C_YELLOW}{EMOJI_WARNING} Selenium: View for '{link_title}' (Port {tor_socks_port}) interrupted by user (Ctrl+C).{C_END}")
        # if driver: driver.save_screenshot(f"ctrl_c_{link_title[:10]}_{tor_socks_port}.png")
        return False, "View interrupted by user (Ctrl+C)"
    except TimeoutException as e:
        error_msg = f"Selenium: Page load timeout or element not found for '{link_title}'. Port: {tor_socks_port}. Error: {str(e).splitlines()[0]}"
        print(f"{C_FAIL}{EMOJI_ERROR} {error_msg}{C_END}")
        # if driver: driver.save_screenshot(f"error_timeout_{link_title[:10]}_{tor_socks_port}.png")
        return False, error_msg
    except WebDriverException as e:
        error_msg = f"Selenium: WebDriverException for '{link_title}'. Port: {tor_socks_port}. Error: {str(e).splitlines()[0]}"
        if "Proxy CONNECT aborted" in str(e) or "SOCKS_PROXY_FAILED" in str(e) or "connection refused" in str(e).lower():
            error_msg = f"Selenium: Tor SOCKS Port {tor_socks_port} connection issue for '{link_title}'. Is Tor running and accessible? Error: {str(e).splitlines()[0]}"
        elif "Reached error page" in str(e):
             error_msg = f"Selenium: Browser reached an error page for '{link_title}' on Port {tor_socks_port}."
        elif "new session" in str(e).lower() or "unable to connect to geckodriver" in str(e).lower():
            error_msg = f"Selenium: Failed to start new browser session or connect to geckodriver on Port {tor_socks_port}. Ensure geckodriver is correctly installed and in PATH. Error: {str(e).splitlines()[0]}"
        print(f"{C_FAIL}{EMOJI_ERROR} {error_msg}{C_END}")
        # if driver: driver.save_screenshot(f"error_webdriver_{link_title[:10]}_{tor_socks_port}.png")
        return False, error_msg
    except Exception as e:
        error_msg = f"Selenium: An unexpected error occurred for '{link_title}'. Port: {tor_socks_port}. Error: {type(e).__name__} - {str(e).splitlines()[0]}"
        print(f"{C_FAIL}{EMOJI_ERROR} {error_msg}{C_END}")
        # if driver: driver.save_screenshot(f"error_unexpected_{link_title[:10]}_{tor_socks_port}.png")
        return False, error_msg
    finally:
        if driver:
            print(f"{C_GRAY}  Selenium: Closing browser for '{link_title}' (Port {tor_socks_port})...{C_END}")
            try:
                driver.quit()
            except Exception as e_quit:
                print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Error during browser quit for port {tor_socks_port}: {type(e_quit).__name__} - {str(e_quit).splitlines()[0]}{C_END}")

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
    original_message = message
    try:
        while not stop_event.is_set() and (duration == 0 or (time.time() - start_time < duration)):
            # Truncate message if too long for a single line with spinner
            max_msg_len = shutil.get_terminal_size((80, 20)).columns - 10
            display_message = original_message
            if len(original_message) > max_msg_len:
                display_message = original_message[:max_msg_len-3] + "..."

            sys.stdout.write(f"\r{color}{emoji} {display_message} {spinner_chars[idx % 4]}{C_END}")
            sys.stdout.flush()
            time.sleep(0.15)
            idx += 1
    except Exception: # Handle cases where terminal size might not be available (e.g. non-interactive env)
        pass # Just stop the spinner on error
    finally: # Ensure spinner line is cleared
        sys.stdout.write("\r" + " " * (shutil.get_terminal_size((80, 20)).columns -1) + "\r")
        sys.stdout.flush()

# --- Animated Banner ---
def print_animated_banner():
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
    ascii_art_content = Text("KADDU ASCII ART MISSING", style="bold red")
    if os.path.exists(ascii_art_path):
        with open(ascii_art_path, 'r', encoding='utf-8') as f:
            # Read the whole art as one block for better centering
            raw_art = f.read()
            # Ensure Rich formatting is applied line by line if needed
            # For pre-formatted ASCII, direct printing with Align might be best.
            # If the ASCII itself contains Rich tags, Text.from_markup might be better.
            ascii_art_content = Text(raw_art, style="bold green") # Apply a base style
    else:
        ascii_art_content = Text("KADDU ASCII ART MISSING", style="bold red")

    # Prepare big 'KADDU' ASCII text using pyfiglet
    kaddu_text_figlet = pyfiglet.figlet_format("KADDU", font="slant")
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
    print(f"{C_BLUE}{EMOJI_INSTALL} Checking Python dependencies (selenium, requests, PySocks, pyfiglet, rich)...{C_END}")
    # Ensure all necessary packages are listed here
    required_modules = {
        "selenium": "selenium", 
        "requests": "requests", 
        "socks": "PySocks", # For requests SOCKS proxy
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
        print(f"\n{C_WARNING}{EMOJI_WARNING} Missing Python packages: {C_BOLD}{missing_packages_str}{C_END}")
        
        req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        if not os.path.exists(req_file):
            print(f"{C_FAIL}{EMOJI_ERROR} {C_BOLD}CRITICAL: 'requirements.txt' not found!{C_END}")
            print(f"{C_WARNING}   Cannot automatically install dependencies. Please create 'requirements.txt' with the following content or install manually:{C_END}")
            # Print out the expected content of requirements.txt
            print(f"{C_GRAY}--- requirements.txt ---{C_END}")
            for pkg in ["selenium", "requests[socks]", "PySocks", "pyfiglet", "rich"]: # Ensure requests[socks] for full SOCKS support
                print(f"{C_GRAY}{pkg}{C_END}")
            print(f"{C_GRAY}------------------------{C_END}")
            print(f"\n{C_YELLOW}{EMOJI_INFO} Manual Installation Guide:{C_END}")
            print(f"{C_CYAN}  1. Create a requirements.txt file with the above content.{C_END}")
            print(f"{C_CYAN}  2. Run: {C_BOLD}pip install -r requirements.txt{C_END}")
            print(f"{C_CYAN}  3. Then re-run: {C_BOLD}python3 main.py{C_END}")
            sys.exit(1)

        print(f"{C_CYAN}{EMOJI_PROMPT} Installing dependencies from '{req_file}'...{C_END}")
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner_animation, args=(f"Installing Python dependencies from {req_file}...", stop_event), kwargs={"emoji": EMOJI_INSTALL, "color": C_CYAN})
        spinner_thread.start()
        try:
            # Use --disable-pip-version-check for cleaner output, --no-input for non-interactive
            proc = subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", req_file], 
                                  capture_output=True, text=True, timeout=240) # Increased timeout
            stop_event.set()
            spinner_thread.join()
            if proc.returncode == 0:
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} All Python dependencies from requirements.txt installed successfully!{C_END}\n")
                # Verify again
                all_installed_now = True
                for module_name in required_modules.keys():
                    try:
                        importlib.import_module(module_name)
                    except ImportError:
                        print(f"{C_FAIL}{EMOJI_ERROR} Package {module_name} still not importable after pip install. Please check pip output and install manually if needed.{C_END}")
                        all_installed_now = False
                if not all_installed_now: sys.exit(1)

            else:
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to install Python dependencies!{C_END}")
                print(f"{C_GRAY}Pip stdout:\n{proc.stdout}{C_END}")
                print(f"{C_GRAY}Pip stderr:\n{proc.stderr}{C_END}")
                print(f"\n{C_YELLOW}{EMOJI_INFO} Manual Installation Guide:{C_END}")
                print(f"{C_CYAN}  1. Ensure you are in your virtual environment (activate it if not).{C_END}")
                print(f"{C_CYAN}  2. Run: {C_BOLD}pip install -r requirements.txt{C_END}")
                print(f"{C_CYAN}  3. If you see errors, try installing missing packages individually, e.g.:{C_END}")
                for pkg in missing_packages:
                    print(f"{C_CYAN}     {C_BOLD}pip install {pkg}{C_END}")
                print(f"{C_CYAN}  4. Then re-run: {C_BOLD}python3 main.py{C_END}")
                sys.exit(1)
        except subprocess.TimeoutExpired:
            stop_event.set()
            spinner_thread.join()
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} pip install timed out after 4 minutes! Check your internet connection or try installing manually.{C_END}")
            print(f"\n{C_YELLOW}{EMOJI_INFO} Manual Installation Guide:{C_END}")
            print(f"{C_CYAN}  1. Ensure you are in your virtual environment (activate it if not).{C_END}")
            print(f"{C_CYAN}  2. Run: {C_BOLD}pip install -r requirements.txt{C_END}")
            print(f"{C_CYAN}  3. If you see errors, try installing missing packages individually, e.g.:{C_END}")
            for pkg in missing_packages:
                print(f"{C_CYAN}     {C_BOLD}pip install {pkg}{C_END}")
            print(f"{C_CYAN}  4. Then re-run: {C_BOLD}python3 main.py{C_END}")
            sys.exit(1)
        except Exception as e:
            stop_event.set()
            spinner_thread.join()
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Exception during dependency installation: {e}{C_END}")
            print(f"\n{C_YELLOW}{EMOJI_INFO} Manual Installation Guide:{C_END}")
            print(f"{C_CYAN}  1. Ensure you are in your virtual environment (activate it if not).{C_END}")
            print(f"{C_CYAN}  2. Run: {C_BOLD}pip install -r requirements.txt{C_END}")
            print(f"{C_CYAN}  3. If you see errors, try installing missing packages individually, e.g.:{C_END}")
            for pkg in missing_packages:
                print(f"{C_CYAN}     {C_BOLD}pip install {pkg}{C_END}")
            print(f"{C_CYAN}  4. Then re-run: {C_BOLD}python3 main.py{C_END}")
            sys.exit(1)
    else:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} All required Python dependencies are already installed!{C_END}\n")

def is_command_available(command):
    return shutil.which(command) is not None

def ensure_tor_installed(): # This now focuses on making 'tor' command available
    print(f"\n{C_BLUE}{EMOJI_TOR} Checking Tor installation ('tor' command availability)...{C_END}")
    if not is_command_available("tor"):
        print(f"{C_WARNING}{EMOJI_WARNING} 'tor' command not found. Attempting to install Tor (may require sudo privileges)...{C_END}")
        installer = None
        install_cmd_update = None
        install_cmd_tor = None
        
        # Determine package manager and commands
        if is_command_available("apt-get"): # Prefer apt-get for non-interactive
            installer = "apt-get"
            install_cmd_update = ["sudo", "apt-get", "update", "-y", "-qq"]
            install_cmd_tor = ["sudo", "apt-get", "install", "tor", "-y", "-qq"]
        elif is_command_available("yum"):
            installer = "yum"
            # yum update can be slow, often not strictly needed just to install one package if repo list is fresh
            # install_cmd_update = ["sudo", "yum", "check-update"] # Optional check
            install_cmd_tor = ["sudo", "yum", "install", "-y", "-q", "tor"]
        elif is_command_available("dnf"): # Fedora
            installer = "dnf"
            install_cmd_tor = ["sudo", "dnf", "install", "-y", "--quiet", "tor"]
        elif is_command_available("pacman"): # Arch
            installer = "pacman"
            # Pacman usually syncs db with -S. --noconfirm for non-interactive
            install_cmd_tor = ["sudo", "pacman", "-S", "--noconfirm", "--quiet", "tor"]
        # Add more package managers if needed (zypper for openSUSE, etc.)

        if installer:
            print(f"{C_CYAN}{EMOJI_PROMPT} Using '{installer}' to install Tor...{C_END}")
            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=spinner_animation, args=(f"Installing Tor with {installer}...", stop_event), kwargs={"emoji": EMOJI_TOR, "color": C_CYAN})
            spinner_thread.start()
            
            success = False
            error_output = ""

            try:
                if install_cmd_update: # For apt-get, run update first
                    proc_update = subprocess.run(install_cmd_update, capture_output=True, stderr=subprocess.PIPE, text=True, timeout=300)
                    if proc_update.returncode != 0:
                        error_output += f"Update failed with {installer}: {proc_update.stderr}\\n"
                    else: # Update successful, proceed to install Tor
                        proc_tor = subprocess.run(install_cmd_tor, capture_output=True, stderr=subprocess.PIPE, text=True, timeout=300)
                        if proc_tor.returncode == 0:
                            success = True
                        else:
                            error_output += f"Tor install failed with {installer}: {proc_tor.stderr}\\n"
                else: # For yum, dnf, pacman - direct install
                    proc_tor = subprocess.run(install_cmd_tor, capture_output=True, stderr=subprocess.PIPE, text=True, timeout=300)
                    if proc_tor.returncode == 0:
                        success = True
                    else:
                        error_output += f"Tor install failed with {installer}: {proc_tor.stderr}\\n"
            except subprocess.TimeoutExpired:
                error_output = f"Tor installation with {installer} timed out after 5 minutes."
                success = False
            except Exception as e:
                error_output = f"Exception during Tor installation with {installer}: {str(e)}"
                success = False
            finally:
                stop_event.set()
                spinner_thread.join()

            if success and is_command_available("tor"):
                print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} Tor command installed successfully using {installer}!{C_END}\n")
            else:
                print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Failed to install 'tor' command using {installer}.{C_END}")
                if error_output.strip():
                    print(f"{C_GRAY}Error details:\n{error_output.strip()}{C_END}")
                print(f"{C_WARNING}{EMOJI_INFO} Please try installing Tor manually for your system (e.g., 'sudo {installer} install tor') and ensure the 'tor' command is in your PATH, then re-run this script.{C_END}")
                print(f"{C_CYAN}{EMOJI_INFO} Download Tor from: https://www.torproject.org/download/{C_END}")
                # Manual install instructions only, no QR code logic
                try:
                    import webbrowser
                    webbrowser.open("https://www.torproject.org/download/")
                except Exception:
                    pass
                sys.exit(1)
        else:
            print(f"\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} Could not detect a supported package manager (apt-get, yum, dnf, pacman) to install Tor.{C_END}")
            print(f"{C_WARNING}{EMOJI_INFO} Please install Tor manually for your system so that the 'tor' command is available in your PATH, then re-run the script.{C_END}")
            print(f"{C_CYAN}{EMOJI_INFO} Download Tor from: https://www.torproject.org/download/{C_END}")
            # Manual install instructions only, no QR code logic
            try:
                import webbrowser
                webbrowser.open("https://www.torproject.org/download/")
            except Exception:
                pass
            sys.exit(1)
    else:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS}{EMOJI_CELEBRATE} 'tor' command is already available!{C_END}\n")

# ensure_tor_service_running() is no longer strictly needed as main.py now prioritizes
# pytor.detect_tor_ports() and pytor.start_tor_instance().
# If pytor is not available, the script will exit.
# If no ports are found and new instances cannot be started, it will also exit.
# So, this function can be simplified or removed if not used by other parts.
# For now, keeping a simplified version that checks for any running Tor process via pgrep.
def check_if_any_tor_process_running():
    """Checks if any 'tor' process is running using pgrep."""
    if not is_command_available("pgrep"):
        # print(f"{C_GRAY}  pgrep command not found, cannot check for existing Tor processes this way.{C_END}")
        return False # Cannot determine
    try:
        pgrep_proc = subprocess.run(["pgrep", "-x", "tor"], capture_output=True, text=True)
        if pgrep_proc.returncode == 0 and pgrep_proc.stdout.strip():
            # print(f"{C_GREEN}  Found existing Tor process(es) with pgrep: {pgrep_proc.stdout.strip()}{C_END}")
            return True
    except Exception: # FileNotFoundError if pgrep/systemctl not found
        # print(f"{C_GRAY}Debug: Exception in is_tor_service_running: {e}{C_END}") # Optional debug
        pass
    # print(f"{C_GRAY}  No existing 'tor' process found by pgrep.{C_END}")
    return False

# --- USER INPUT FUNCTIONS (Implemented) ---
def get_user_links():
    print(f"\n{C_BLUE}{EMOJI_PROMPT} {C_BOLD}Enter YouTube Video Links{C_END}")
    print(f"{C_CYAN}  Please enter the full YouTube video URLs one by one. Type 'done' when finished, or 'quit' to exit.{C_END}")
    links = []
    while True:
        link = input(f"{C_YELLOW}  {EMOJI_LINK} URL (or 'done'/'quit'): {C_END}").strip()
        if link.lower() == 'done':
            if not links:
                print(f"{C_WARNING}{EMOJI_WARNING} No links entered. Please provide at least one link or type 'quit'.{C_END}")
            else:
                break
        elif link.lower() == 'quit':
            print(f"{C_FAIL}{EMOJI_FAIL} User requested quit. Exiting script.{C_END}")
            sys.exit(0)
        elif ("youtube.com/" in link or "youtu.be/" in link) and ("http://" in link or "https://" in link) :
            # Basic validation for YouTube link structure
            if not re.match(r"^https?://(www\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)[a-zA-Z0-9_\-]+.*", link):
                print(f"{C_FAIL}{EMOJI_ERROR} Invalid YouTube URL format. Please use a full URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID).{C_END}")
                continue
            links.append(link)
            print(f"{C_GREEN}    {EMOJI_SUCCESS} Link added: {link[:60]}{'...' if len(link)>60 else ''}{C_END}")
        else:
            print(f"{C_FAIL}{EMOJI_ERROR} Invalid link. Please enter a valid YouTube URL (e.g., https://www.youtube.com/watch?v=...) or 'done'/'quit'.{C_END}")
    if links:
        print(f"\n{C_GREEN}{EMOJI_SUCCESS} {len(links)} link(s) collected successfully.{C_END}")
    return links

def get_views_per_link():
    print(f"\n{C_BLUE}{EMOJI_PROMPT} {C_BOLD}Number of Views per Link{C_END}")
    while True:
        try:
            views_str = input(f"{C_YELLOW}  {EMOJI_VIEW} How many views per link? (e.g., 10, or type 'quit'): {C_END}").strip()
            if views_str.lower() == 'quit':
                print(f"{C_FAIL}{EMOJI_FAIL} User requested quit. Exiting script.{C_END}")
                sys.exit(0) # Return None to indicate quit, main loop should handle
            views = int(views_str)
            if views > 0:
                print(f"{C_GREEN}    {EMOJI_SUCCESS} Each link will be targeted for {views} views.{C_END}")
                return views
            else:
                print(f"{C_FAIL}{EMOJI_ERROR} Please enter a positive number of views.{C_END}")
        except ValueError:
            print(f"{C_FAIL}{EMOJI_ERROR} Invalid input. Please enter a number.{C_END}")

def get_connection_count():
    print(f"\n{C_BLUE}{EMOJI_PROMPT} {C_BOLD}Number of Parallel Connections{C_END}")
    print(f"{C_CYAN}  This script will attempt to use this many Tor circuits simultaneously.{C_END}")
    print(f"{C_CYAN}  It will try to detect existing Tor ports or start new user-space instances.{C_END}")
    max_sensible_connections = 20 # Arbitrary limit to suggest to user, can be adjusted
    while True:
        try:
            num_str = input(f"{C_YELLOW}  {EMOJI_THREADS} How many parallel connections? (1-{max_sensible_connections}, or 'quit'): {C_END}").strip()
            if num_str.lower() == 'quit':
                print(f"{C_FAIL}{EMOJI_FAIL} User requested quit. Exiting script.{C_END}")
                sys.exit(0) # Return None to indicate quit
            num = int(num_str)
            if 0 < num <= max_sensible_connections:
                print(f"{C_GREEN}    {EMOJI_SUCCESS} Requesting {num} parallel connection(s). Actual may be lower based on available Tor ports.{C_END}")
                return num
            elif num > max_sensible_connections:
                 print(f"{C_WARNING}{EMOJI_WARNING} Requesting more than {max_sensible_connections} connections may significantly tax your system and network, or overload Tor circuits.{C_END}")
                 confirm_high = input(f"{C_YELLOW}  Are you sure you want to proceed with {num} connections? This is not generally recommended. (yes/no): {C_END}").strip().lower()
                 if confirm_high in ['yes', 'y']:
                    print(f"{C_GREEN}    {EMOJI_SUCCESS} Proceeding with {num} parallel connection(s) as requested.{C_END}")
                    return num
                 else:
                    print(f"{C_CYAN}    Request for {num} connections cancelled by user. Please enter a new value.{C_END}") 
            else: # num <= 0
                print(f"{C_FAIL}{EMOJI_ERROR} Please enter a positive number of connections (1-{max_sensible_connections}).{C_END}")
        except ValueError:
            print(f"{C_FAIL}{EMOJI_ERROR} Invalid input. Please enter a number.{C_END}")

def get_dry_run_choice():
    print(f"\n{C_BLUE}{EMOJI_PROMPT} {C_BOLD}Dry Run Option{C_END}")
    print(f"{C_CYAN}  A dry run will simulate the setup and estimate tasks without actual video views or prolonged Tor usage.{C_END}")
    while True:
        choice = input(f"{C_YELLOW}  {EMOJI_DRY_RUN} Perform a dry run? (yes/no, or 'quit'): {C_END}").strip().lower()
        if choice.lower() == 'quit':
            print(f"{C_FAIL}{EMOJI_FAIL} User requested quit. Exiting script.{C_END}")
            sys.exit(0) # No return value needed as main will exit
        if choice in ['yes', 'y']:
            print(f"{C_GREEN}    {EMOJI_SUCCESS} Dry run selected. No actual views will be generated.{C_END}")
            return True
        elif choice in ['no', 'n']:
            print(f"{C_GREEN}    {EMOJI_SUCCESS} Actual view generation selected. {C_BOLD}Videos will be watched via Tor.{C_END}")
            return False
        else:
            print(f"{C_FAIL}{EMOJI_ERROR} Invalid input. Please type 'yes' or 'no'.{C_END}")

# --- VALIDATION AND PROCESSING FUNCTIONS (Implemented) ---
def validate_link_with_tor(link_url, tor_port, link_title="N/A"):
    """
    Validates a single link by trying to access it via Tor using Selenium (minimal interaction).
    Enhanced privacy options for non-detectability. Uses a short validation duration.
    """
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.set_preference("general.useragent.override", get_random_user_agent())
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", int(tor_port))
    options.set_preference("network.proxy.socks_remote_dns", True)
    options.set_preference("media.volume_scale", "0.0")
    # Enhanced privacy options
    options.set_preference("media.peerconnection.enabled", False)
    options.set_preference("geo.enabled", False)
    options.set_preference("privacy.trackingprotection.enabled", True)
    options.set_preference("privacy.trackingprotection.fingerprinting.enabled", True)
    options.set_preference("privacy.trackingprotection.cryptomining.enabled", True)
    options.set_preference("privacy.donottrackheader.enabled", True)
    options.set_preference("network.cookie.cookieBehavior", 5)
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    # options.set_preference("privacy.resistFingerprinting", True) # Can break sites
    driver = None
    validation_watch_duration = 10 # seconds, short for validation
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(60)
        print(f"{C_GRAY}  Selenium: Navigating to {link_url} via Tor port {tor_port}...{C_END}")
        driver.get(link_url)
        print(f"{C_GRAY}  Selenium: Waiting for video element or YouTube page title...{C_END}")
        WebDriverWait(driver, 20).until(
             EC.any_of(
                EC.presence_of_element_located((By.TAG_NAME, "video")),
                EC.title_contains("YouTube") 
            )
        )
        print(f"{C_GREEN}  Selenium: Page appears loaded (video or YT title found).{C_END}")
        
        # Handle cookie consent pop-ups (improved with more generic selectors)
        consent_selectors = [
            "//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]]", # Covers "Accept all" in a span
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree to all')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'i agree')]",
            "//button[@id='L2AGLb']", # Google's specific ID
            "//div[@role='dialog']//button[contains(text(), 'Accept') or contains(text(), 'Agree') or contains(text(), 'Allow')]", # More generic
            "form[action*='consent.youtube.com'] button" # Form based consent
        ]
        for i, selector in enumerate(consent_selectors):
            try:
                consent_button = WebDriverWait(driver, 3).until( # Short timeout for each attempt
                    EC.element_to_be_clickable((By.XPATH if selector.startswith("//") else By.CSS_SELECTOR, selector))
                )
                print(f"{C_GRAY}  Selenium: Found potential consent button (selector #{i}). Clicking...{C_END}")
                driver.execute_script("arguments[0].click();", consent_button) # JS click can be more robust
                # consent_button.click()
                print(f"{C_GREEN}  Selenium: Clicked consent button.{C_END}")
                time.sleep(random.uniform(2, 4)) # Wait for pop-up to disappear/page to react
                break 
            except TimeoutException:
                if i == len(consent_selectors) - 1:
                    print(f"{C_GRAY}  Selenium: No generic consent pop-up button found or needed within timeout.{C_END}")
            except Exception as e_consent:
                print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Minor error trying to click consent button (Selector #{i}): {str(e_consent).splitlines()[0]}{C_END}")
        
        # Attempt to click the main play button on YouTube if video is not auto-playing
        try:
            video_element = driver.find_element(By.TAG_NAME, "video")
            # Check if video is paused (JavaScript check)
            # Note: This might not work perfectly due to YouTube's complex player states
            is_paused = driver.execute_script("return arguments[0].paused;", video_element)

            if is_paused:
                print(f"{C_GRAY}  Selenium: Video detected as paused. Attempting to click play button...{C_END}")
                play_button_selectors = [
                    "button.ytp-large-play-button.ytp-button", # Main large play button
                    "button[aria-label='Play (k)']",           # Play button with aria-label
                    ".html5-main-video"                         # Clicking the video element itself
                ]
                play_button_clicked = False
                for selector in play_button_selectors:
                    try:
                        play_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        if play_button and play_button.is_displayed():
                            # play_button.click()
                            driver.execute_script("arguments[0].click();", play_button)
                            print(f"{C_GREEN}  Selenium: Clicked video play button (selector: {selector}).{C_END}")
                            play_button_clicked = True
                            break
                    except Exception: # Timeout or other error
                        pass # Try next selector
                if not play_button_clicked:
                    print(f"{C_GRAY}  Selenium: Could not find/click a play button, or video started playing automatically.{C_END}")
            else:
                print(f"{C_GRAY}  Selenium: Video appears to be playing or autoplaying.{C_END}")

        except TimeoutException:
            print(f"{C_GRAY}  Selenium: Video play button not found or not clickable (might be autoplaying or structure changed).{C_END}")
        except Exception as e_play:
            print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Minor error interacting with play button: {str(e_play)[:100]}{C_END}")

        # Simulate watch time with slight variation
        actual_watch_duration = validation_watch_duration + random.uniform(-2, 2)
        actual_watch_duration = max(5, int(actual_watch_duration))
        print(f"{C_GRAY}  Selenium: Simulating watch time for ~{actual_watch_duration} seconds...{C_END}")
        start_watch_time = time.time()
        while time.time() - start_watch_time < actual_watch_duration:
            if stop_event_global.is_set():
                print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Watch time for '{link_title}' interrupted by stop signal.{C_END}")
                return False, "Watch interrupted by stop signal"
            time.sleep(1)
        print(f"{C_GREEN}{EMOJI_SUCCESS} Selenium: Successfully simulated view for '{link_title}' for {actual_watch_duration}s.{C_END}")
        return True, f"Watched for {actual_watch_duration}s"
    except (TimeoutException, WebDriverException) as e:
        error_msg = f"Selenium: Page load timeout or element not found for '{link_title}'. Port: {tor_port}. Error: {str(e).splitlines()[0]}"
        print(f"{C_FAIL}{EMOJI_ERROR} {error_msg}{C_END}")
        return False, error_msg
    except Exception as e_gen:
        error_msg = f"Selenium: An unexpected error occurred for '{link_title}'. Port: {tor_port}. Error: {type(e_gen).__name__} - {str(e_gen).splitlines()[0]}"
        print(f"{C_FAIL}{EMOJI_ERROR} {error_msg}{C_END}")
        return False, error_msg
    finally:
        if driver:
            print(f"{C_GRAY}  Selenium: Closing browser for '{link_title}' (Port {tor_port})...{C_END}")
            try:
                driver.quit()
            except Exception as e_quit:
                print(f"{C_YELLOW}{EMOJI_WARNING} Selenium: Error during browser quit: {type(e_quit).__name__} - {str(e_quit).splitlines()[0]}{C_END}")

def validate_all_links(links_data_list, tor_ports):
    print(f"\n{C_BLUE}{EMOJI_SEARCH} {C_BOLD}Validating All Links via Tor...{C_END}")
    if not links_data_list:
        print(f"{C_WARNING}{EMOJI_WARNING} No links provided to validate.{C_END}")
        return []
    if not tor_ports:
        print(f"{C_FAIL}{EMOJI_ERROR} No Tor ports available for link validation. Cannot proceed.{C_END}")
        return []

    validation_port = random.choice(tor_ports)
    print(f"{C_CYAN}  Using Tor SOCKS Port {validation_port} for validation process.{C_END}")
    
    valid_links_data = []
    for i, link_data in enumerate(links_data_list):
        if stop_event_global.is_set():
            print(f"\n{C_WARNING}{EMOJI_WARNING} Validation interrupted by user.{C_END}")
            break
        print(f"{C_CYAN}  ({i+1}/{len(links_data_list)}) Validating: {link_data['title']}... {C_END}", end="") # Moved print here
        is_valid = validate_link_with_tor(link_data['url'], validation_port, link_data['title']) # validate_link_with_tor will print its own result now
        if is_valid:
            valid_links_data.append(link_data)
        time.sleep(random.uniform(0.5, 1.5)) 

    if not stop_event_global.is_set(): # Only print summary if not interrupted
        if valid_links_data:
            print(f"\n{C_GREEN}{EMOJI_SUCCESS} Validation complete: {len(valid_links_data)} out of {len(links_data_list)} links are valid and accessible.{C_END}")
        else:
            print(f"\n{C_FAIL}{EMOJI_ERROR} Validation complete: No valid/accessible links found.{C_END}")
    return valid_links_data

def dry_run_summary(links_data, views_per_link, num_connections, tor_ports_to_use):
    """
    Prints a summary of what the script would do in a dry run.
    """
    print(f"\\n{C_HEADER}{EMOJI_DRY_RUN} --- KADDU YT-VIEWS: DRY RUN SUMMARY --- {EMOJI_DRY_RUN}{C_END}")
    print(f"{C_CYAN}The script is configured as follows (NO actual views will be generated):{C_END}")
    print(f"{C_BLUE}  {EMOJI_VIDEO} Links to process: {len(links_data)}{C_END}")
    for i, link_data in enumerate(links_data):
        link_type = "YouTube Short" if link_data['is_short'] else "YouTube Video"
        print(f"{C_GRAY}    {i+1}. '{link_data['title']}' ({link_data['url'][:50]}...) - Type: {link_type}{C_END}")
    print(f"{C_BLUE}  {EMOJI_VIEW} Target views per link: {views_per_link}{C_END}")
    print(f"{C_BLUE}  {EMOJI_THREADS} Requested parallel connections: {num_connections}{C_END}")
    if tor_ports_to_use:
        print(f"{C_BLUE}  {EMOJI_TOR} Tor SOCKS ports intended for use: {tor_ports_to_use}{C_END}")
    else:
        print(f"{C_WARNING}  {EMOJI_TOR} No Tor SOCKS ports currently identified for use (this might be resolved in actual run).{C_END}")

    total_potential_views = len(links_data) * views_per_link
    print(f"{C_BLUE}  {EMOJI_GEAR} Total potential view simulations planned: {total_potential_views}{C_END}")

    # Estimate watch times based on view_worker logic
    avg_video_watch_time_base = (45 + 120) / 2 # Average of min/max from view_worker
    avg_short_watch_time_base = (15 + 40) / 2  # Average of min/max from view_worker
    
    estimated_total_watch_seconds = 0
    for link_data in links_data:
        watch_time = avg_short_watch_time_base if link_data['is_short'] else avg_video_watch_time_base
        estimated_total_watch_seconds += watch_time * views_per_link
        
    avg_overhead_per_view = 75 
    total_overhead_seconds = total_potential_views * avg_overhead_per_view
    total_simulation_seconds = estimated_total_watch_seconds + total_overhead_seconds
    
    if num_connections > 0 and total_potential_views > 0:
        estimated_duration_seconds = total_simulation_seconds / num_connections 
    elif total_potential_views > 0:
        estimated_duration_seconds = total_simulation_seconds
    else:
        estimated_duration_seconds = 0

    time_str = "N/A"
    if estimated_duration_seconds > 0:
        time_str = time.strftime("%H hours, %M minutes, %S seconds", time.gmtime(estimated_duration_seconds))
    
    print(f"{C_BLUE}  {EMOJI_WAIT} Estimated execution time for these tasks (VERY ROUGH): {C_BOLD}{time_str}{C_END}")
    print(f"{C_GRAY}    (Actual time for a real run will depend on network conditions, Tor speed, system load, and YouTube's responses.){C_END}")
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")

def view_worker(link_data, tor_socks_port, view_num_for_link, total_views_for_link, overall_task_num, total_overall_tasks):
    """
    Worker function executed by each thread to simulate a single view.
    """
    global overall_completed_views_total, overall_failed_attempts_total

    if stop_event_global.is_set():
        return False, "Stopped by global event before start"

    video_url = link_data['url']
    link_title = link_data['title'] 
    is_short = link_data['is_short']

    base_watch_video = random.randint(45, 120)
    base_watch_short = random.randint(15, 40)
    watch_duration = base_watch_short if is_short else base_watch_video
    
    time.sleep(random.uniform(0.5, 2.5)) 

    task_progress_str = f"(Task {overall_task_num}/{total_overall_tasks} | Link '{link_title}' View {view_num_for_link}/{total_views_for_link})"
    print(f"{C_CYAN}{EMOJI_VIEW} {task_progress_str} Starting via Port {tor_socks_port} for ~{watch_duration}s...{C_END}")

    success, message = simulate_view_with_selenium(video_url, tor_socks_port, watch_duration, f"{link_title} {task_progress_str}")

    with completed_views_lock:
        if success:
            overall_completed_views_total += 1
            print(f"{C_GREEN}{EMOJI_SUCCESS} {task_progress_str} COMPLETED on Port {tor_socks_port}. ({message}){C_END}")
        else:
            overall_failed_attempts_total += 1
            print(f"{C_FAIL}{EMOJI_ERROR} {task_progress_str} FAILED on Port {tor_socks_port}. ({message}){C_END}")
    
    if not stop_event_global.is_set():
        time.sleep(random.uniform(2, 5))
    
    if random.random() < 0.03:
        if not stop_event_global.is_set():
            print(f"{C_CYAN}{EMOJI_INFO} [Infotainment from Worker] {get_random_infotainment()}{C_END}")

    return success, message

def create_and_run_threads(links_data, views_per_link, num_connections, tor_ports_to_use):
    """
    Creates and manages a pool of threads to simulate views.
    """
    print(f"\\n{C_HEADER}{EMOJI_THREADS} {C_BOLD}Initiating View Generation Process{C_END}")
    print(f"{C_CYAN}  Targeting {views_per_link} views for each of the {len(links_data)} link(s).{C_END}")
    print(f"{C_CYAN}  Will use {num_connections} parallel worker(s) across Tor ports: {tor_ports_to_use}{C_END}")
    
    if not links_data or not tor_ports_to_use or num_connections == 0:
        print(f"{C_FAIL}{EMOJI_ERROR} Cannot start view generation: Missing links, Tor ports, or connections specified.{C_END}")
        return

    all_view_tasks_details = []
    total_overall_tasks_count = len(links_data) * views_per_link
    current_overall_task_num = 0
    for link_item in links_data:
        for i in range(1, views_per_link + 1):
            current_overall_task_num += 1
            all_view_tasks_details.append((link_item, i, views_per_link, current_overall_task_num, total_overall_tasks_count))
    
    random.shuffle(all_view_tasks_details)

    port_cycler = itertools.cycle(tor_ports_to_use)
    submitted_tasks_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_connections) as executor:
        future_to_task = {} # To map future back to task details for logging if needed
        
        for task_link_data, task_view_num, task_total_views in all_view_tasks:
            if stop_event_global.is_set():
                print(f"{C_WARNING}{EMOJI_WARNING} Global stop signal received. No more tasks will be submitted.{C_END}")
                break
            
            current_tor_port = next(port_cycler)
            future = executor.submit(view_worker, task_link_data, current_tor_port, task_view_num, task_total_views)
            future_to_task[future] = f"View {task_view_num} for {task_link_data['title'][:30]}"
            submitted_tasks +=1
            
            # Brief pause between submitting tasks to avoid bursting Tor connections
            time.sleep(random.uniform(0.2, 0.8)) 

        print(f"\n{C_BLUE}{EMOJI_WAIT} All {submitted_tasks}/{total_tasks_to_submit} view tasks submitted to workers. Monitoring completion... (Ctrl+C to signal stop){C_END}")
        
        # Wait for futures to complete, respecting stop_event_global
        try:
            for future in concurrent.futures.as_completed(future_to_task.keys()):
                task_desc = future_to_task[future]
                if stop_event_global.is_set():
                    # print(f"{C_YELLOW}  Task {task_desc} completion check skipped due to stop signal.{C_END}")
                    pass # Worker itself checks stop_event_global
                try:
                    future.result(timeout=1) # Check result briefly, but don't hang if worker is stuck despite stop_event
                except concurrent.futures.CancelledError:
                    print(f"{C_GRAY}  Task {task_desc} was cancelled.{C_END}")
                except concurrent.futures.TimeoutError:
                    pass # Worker is still running, or finished and we missed it.
                except Exception as exc:
                    print(f"{C_FAIL}{EMOJI_ERROR} Task {task_desc} generated an error: {exc}{C_END}")
                
                if stop_event_global.is_set() and executor._work_queue.qsize() == 0 and len(executor._threads) == 0:
                     print(f"{C_YELLOW} Stop signal active and executor queue empty/threads winding down.{C_END}")
                     break

        except KeyboardInterrupt: # Handle Ctrl+C during as_completed
            print(f"\n{C_WARNING}{EMOJI_WARNING} Keyboard interrupt during task monitoring. Signaling stop to all workers...{C_END}")
            stop_event_global.set()
            # Give workers a moment to react to the stop_event_global
            time.sleep(5) 
            # executor.shutdown(wait=True, cancel_futures=True) # Py3.9+ for cancel_futures
            executor.shutdown(wait=True) # Shutdown remaining threads

    if stop_event_global.is_set():
        print(f"\n{C_WARNING}{EMOJI_WARNING} View generation process was interrupted.{C_END}")
    else:
        print(f"\n{C_GREEN}{EMOJI_CELEBRATE} All submitted view generation tasks have been processed.{C_END}")

def estimate_total_time(links_data, views_per_link, num_connections):
    if not links_data or num_connections == 0 or views_per_link == 0:
        print(f"\n{C_BLUE}{EMOJI_WAIT} {C_BOLD}Estimated Total Time{C_END}")
        print(f"{C_CYAN}  Cannot estimate time: No links, views, or connections specified.{C_END}")
        return True # Allow to proceed to confirmation, where it might be caught.

    # Average estimates (these are very rough)
    avg_selenium_overhead_per_view = random.uniform(40, 70) # Page load, cookie handling, play button, quit
    avg_random_delays_per_view = random.uniform(3, 8) # Delays between views/actions
    
    total_tasks = len(links_data) * views_per_link
    
    total_estimated_seconds_for_all_tasks = 0
    for link_data in links_data:
        is_short = link_data['is_short']
        # Use average of the random ranges from view_worker
        avg_watch_duration = ((15 + 40) / 2) if is_short else ((45 + 120) / 2)
        
        time_per_single_view = avg_selenium_overhead_per_view + avg_watch_duration + avg_random_delays_per_view
        total_estimated_seconds_for_all_tasks += time_per_single_view * views_per_link

    if num_connections > 0:
        effective_total_seconds = total_estimated_seconds_for_all_tasks / num_connections
    elif total_tasks > 0: # Avoid division by zero if somehow num_connections is 0
        effective_total_seconds = total_estimated_seconds_for_all_tasks
    else:
        effective_total_seconds = 0

    time_str = time.strftime("%H hours, %M minutes, %S seconds", time.gmtime(effective_total_seconds))

    print(f"\n{C_BLUE}{EMOJI_WAIT} {C_BOLD}Estimated Total Time{C_END}")
    print(f"{C_CYAN}  Based on your settings ({total_tasks} total views), the estimated time is roughly: {C_BOLD}{time_str}{C_END}")
    print(f"{C_GRAY}    (Actual time will depend heavily on network, Tor, system load, and YouTube's behavior.){C_END}")
    print(f"{C_CYAN}[Infotainment] {get_random_infotainment()}{C_END}")
    return True # Always return true to allow user to confirm

def get_user_confirmation_to_proceed():
    print(f"\n{C_YELLOW}{EMOJI_PROMPT} {C_BOLD}Ready to start the YouTube view generation process?{C_END}")
    while True:
        choice = input(f"{C_WARNING}  {EMOJI_ROCKET} Proceed with generating views? (yes/no, or 'quit'): {C_END}").strip().lower()
        if choice.lower() == 'quit':
            print(f"{C_FAIL}{EMOJI_FAIL} User requested quit. Exiting script.{C_END}")
            return False # Signal to exit
        if choice in ['yes', 'y']:
            print(f"{C_GREEN}{EMOJI_SUCCESS} User confirmed. Initiating view generation... Strap in! {EMOJI_ROCKET}{C_END}")
            return True
        elif choice in ['no', 'n']:
            print(f"{C_FAIL}{EMOJI_FAIL} User cancelled the operation. Exiting script.{C_END}")
            return False
        else:
            print(f"{C_FAIL}{EMOJI_ERROR} Invalid input. Please type 'yes' or 'no'.{C_END}")

# --- MAIN FUNCTION ---
def main():
    global overall_completed_views_total, overall_failed_attempts_total
    overall_completed_views_total = 0 
    overall_failed_attempts_total = 0
    stop_event_global.clear() # Ensure stop event is clear at the start of a new run

    # 1. Initial Setup & Welcome
    print_animated_banner()
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    require_venv_or_exit()
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    check_root()
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    check_and_install_python_dependencies()
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    ensure_geckodriver_available()
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")
    ensure_tor_installed()
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")

    # 2. Check for Pytor Module (Crucial for advanced Tor management)
    if not pytor: # pytor is imported at the top of the file
        print(f"{C_FAIL}{EMOJI_ERROR} CRITICAL: The 'pytor.py' module is not available or failed to import.{C_END}")
        print(f"{C_WARNING}  This script relies on 'pytor.py' for advanced Tor instance management (starting, stopping, IP rotation).{C_END}")
        print(f"{C_CYAN}  Please ensure 'pytor.py' is in the same directory as 'main.py'. Exiting.{C_END}")
        sys.exit(1)
    else:
        print(f"{C_GREEN}{EMOJI_SUCCESS} 'pytor.py' module loaded successfully.{C_END}")
    
    # Informational check for any existing Tor processes (pgrep based)
    if check_if_any_tor_process_running():
        print(f"{C_GREEN}{EMOJI_INFO} An existing Tor process seems to be running on the system (detected via pgrep).{C_END}")
        print(f"{C_CYAN}  This script will attempt to use its own managed Tor instances or auto-detected ports.{C_END}")
    else:
        print(f"{C_YELLOW}{EMOJI_INFO} No obvious existing Tor process found by pgrep. Script will manage its own Tor instances.{C_END}")


    # 3. Get User Inputs
    print(f"\\n{C_HEADER}{EMOJI_PROMPT} --- GATHERING YOUR REQUIREMENTS --- {EMOJI_PROMPT}{C_END}")
    user_links_input = get_user_links()
    if not user_links_input: # Function handles its own quit, but double check for empty list
        print(f"{C_FAIL}{EMOJI_ERROR} No YouTube links were provided. Cannot proceed. Exiting.{C_END}")
        sys.exit(1)
    
    views_count_per_link = get_views_per_link()
    # get_views_per_link handles its own quit logic

    num_connections_requested = get_connection_count()
    # get_connection_count handles its own quit logic

    is_dry_run = get_dry_run_choice()
    # get_dry_run_choice handles its own quit logic

    # 4. Tor Setup and Port Management using Pytor
    print(f"\\n{C_HEADER}{EMOJI_TOR} --- KADDU YT-VIEWS TOR NETWORK SETUP --- {EMOJI_TOR}{C_END}")
    managed_tor_instances_details = [] # To store details of Tor instances started by this script
    operational_ports = []
    
    # Step 4a: Detect any already running Tor SOCKS ports (system or user-started)
    print(f"{C_CYAN}{EMOJI_SEARCH} Detecting existing operational Tor SOCKS ports (using pytor.detect_tor_ports)...{C_END}")
    try:
        existing_ports = pytor.detect_tor_ports(start_port=9050, end_port=9070, verbose_scan=False) 
        if existing_ports:
            print(f"{C_GREEN}{EMOJI_SUCCESS} Found {len(existing_ports)} existing operational Tor SOCKS port(s): {sorted(list(set(existing_ports)))}{C_END}")
            operational_ports.extend(existing_ports)
        else:
            print(f"{C_YELLOW}{EMOJI_INFO} No pre-existing operational Tor SOCKS ports detected by pytor in the checked range.{C_END}")
    except Exception as e:
        print(f"{C_FAIL}{EMOJI_ERROR} Error during pytor Tor port detection: {e}{C_END}")
        print(f"{C_WARNING} Will proceed assuming no existing system ports, and will try to start new user-space instances.{C_END}")

    # Step 4b: If more ports are needed, try to start user-space Tor instances with pytor
    actual_num_connections = num_connections_requested
    if len(set(operational_ports)) < num_connections_requested:
        ports_to_start_count = num_connections_requested - len(set(operational_ports))
        print(f"{C_CYAN}{EMOJI_GEAR} Need to start {ports_to_start_count} new user-space Tor instance(s) to meet the {num_connections_requested} connection requirement.{C_END}")
        
        if hasattr(pytor, 'ensure_tor_binary'):
             if not pytor.ensure_tor_binary():
                print(f"{C_FAIL}{EMOJI_ERROR} 'tor' binary not found by pytor. Cannot start new Tor instances. Exiting.{C_END}")
                if managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
                sys.exit(1)
        elif not is_command_available("tor"):
            print(f"{C_FAIL}{EMOJI_ERROR} 'tor' command not found in PATH. Cannot start new Tor instances. Exiting.{C_END}")
            if managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
            sys.exit(1)

        for i in range(ports_to_start_count):
            if stop_event_global.is_set(): 
                print(f"{C_WARNING}{EMOJI_WARNING} Tor instance startup interrupted by user.{C_END}")
                break
            print(f"{C_BLUE}{EMOJI_CONNECTING} Attempting to start user-space Tor instance #{i+1} of {ports_to_start_count} (using pytor.py)...{C_END}")
            try:
                start_search_port_socks = 9150 + (len(managed_tor_instances_details) * 10)
                start_search_port_control = start_search_port_socks + 1

                instance_details = pytor.start_tor_instance(
                    socks_port=None, 
                    control_port=None, 
                    torrc_custom_settings=None, 
                    auto_find_ports_start_socks=start_search_port_socks,
                    auto_find_ports_start_control=start_search_port_control
                )

                if instance_details and instance_details.get('socks_port'):
                    if pytor.verify_tor_instance(instance_details, timeout=120):
                        new_port = instance_details['socks_port']
                        print(f"{C_GREEN}{EMOJI_SUCCESS} User-space Tor instance #{i+1} started and verified successfully on SOCKS Port: {new_port} (PID: {instance_details.get('pid', 'N/A')}){C_END}")
                        operational_ports.append(new_port)
                        managed_tor_instances_details.append(instance_details)
                        if len(set(operational_ports)) >= num_connections_requested: break
                    else: # This is the specific else block to fix for indentation
                        print(f"{C_FAIL}{EMOJI_ERROR} Failed to verify newly started user-space Tor instance #{i+1} (SOCKS Port: {instance_details.get('socks_port', 'N/A')}).{C_END}")
                        if instance_details: pytor.cleanup_tor_instances([instance_details])
                else:
                    print(f"{C_FAIL}{EMOJI_ERROR} Failed to start user-space Tor instance #{i+1}. `pytor.start_tor_instance` returned None or no SOCKS port.{C_END}")
            except Exception as e_start:
                print(f"{C_FAIL}{EMOJI_ERROR} Exception while trying to start user-space Tor instance #{i+1}: {e_start}{C_END}")
                import traceback
                print(f"{C_GRAY}{traceback.format_exc()[:300]}...{C_END}")
    
    # Step 4c: Final check and selection of ports to use.
    if not operational_ports:
        print(f"\\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} CRITICAL: No Tor SOCKS ports are operational after all attempts.{C_END}")
        if pytor and managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
        sys.exit(1)

    tor_ports_to_use = sorted(list(set(operational_ports)))[:num_connections_requested] 
    actual_num_connections = len(tor_ports_to_use)
    
    if actual_num_connections == 0:
        print(f"\\n{C_FAIL}{EMOJI_ERROR}{EMOJI_FAIL} CRITICAL: No operational Tor ports available. Exiting.{C_END}")
        if pytor and managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
        sys.exit(1)
    elif actual_num_connections < num_connections_requested:
        print(f"\\n{C_WARNING}{EMOJI_WARNING} Only {actual_num_connections} unique Tor SOCKS port(s) available ({tor_ports_to_use}), not {num_connections_requested}.{C_END}")
        print(f"{C_CYAN}   Proceeding with these {actual_num_connections} connection(s).{C_END}")
    else:
        print(f"\\n{C_GREEN}{EMOJI_SUCCESS} Successfully configured {actual_num_connections} Tor SOCKS port(s): {tor_ports_to_use}{C_END}")

    # 5. Link Data Preparation & Validation
    print(f"\\n{C_HEADER}{EMOJI_LINK} {C_BOLD}PREPARING AND VALIDATING LINKS...{C_END}")
    links_data_for_processing = []
    for i, link_url_from_user in enumerate(user_links_input):
        parsed_url = urlparse(link_url_from_user)
        video_id_match = re.search(r"(?:v=|/embed/|/shorts/|youtu\.be/)([a-zA-Z0-9_\-]{11})", link_url_from_user)
        video_id_or_slug = video_id_match.group(1) if video_id_match else f"customID{i+1}"
        simple_title = f"Video_{video_id_or_slug}"
        is_short_link = "shorts" in parsed_url.path.lower() or "/shorts/" in link_url_from_user.lower()
        links_data_for_processing.append({
            'id': i, 'url': link_url_from_user, 'title': simple_title, 'is_short': is_short_link 
        })

    validated_links_data = validate_all_links(links_data_for_processing, tor_ports_to_use)
    if not validated_links_data:
        print(f"\\n{C_FAIL}{EMOJI_ERROR} No valid YouTube links after validation. Exiting.{C_END}")
        if pytor and managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
        sys.exit(1)

    # 6. Dry Run or Actual Execution Logic
    if is_dry_run:
        dry_run_summary(validated_links_data, views_count_per_link, actual_num_connections, tor_ports_to_use)
        if pytor and managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
        print(f"\\n{C_GREEN}{EMOJI_DRY_RUN} Dry run concluded. Exiting KADDU YT-VIEWS.{C_END}")
        sys.exit(0)

    print(f"\\n{C_HEADER}{EMOJI_ROCKET} --- PREPARING FOR ACTUAL VIEW GENERATION --- {EMOJI_ROCKET}{C_END}")
    estimate_total_time(validated_links_data, views_count_per_link, actual_num_connections)
    
    if not get_user_confirmation_to_proceed():
        if pytor and managed_tor_instances_details: pytor.cleanup_tor_instances(managed_tor_instances_details)
        print(f"{C_CYAN}Operation cancelled by user. Exiting KADDU YT-VIEWS.{C_END}")
        sys.exit(0)

    # 7. Create and Run Viewing Threads
    overall_completed_views_total = 0 
    overall_failed_attempts_total = 0
    stop_event_global.clear()

    create_and_run_threads(validated_links_data, views_count_per_link, actual_num_connections, tor_ports_to_use)

    # 8. FINAL SUMMARY
    print(f"\\n{C_HEADER}{EMOJI_BANNER} --- KADDU YT-VIEWS FINAL SUMMARY --- {EMOJI_BANNER}{C_END}")
    print(f"{C_OKGREEN}{EMOJI_SUCCESS} Total successful views recorded: {overall_completed_views_total}{C_END}")
    print(f"{C_FAIL}{EMOJI_ERROR} Total failed view attempts recorded: {overall_failed_attempts_total}{C_END}")
    total_tasks_processed_or_attempted = overall_completed_views_total + overall_failed_attempts_total
    target_total_views = len(validated_links_data) * views_count_per_link
    if target_total_views > 0 :
        success_rate = (overall_completed_views_total / target_total_views) * 100 if target_total_views > 0 else 0
        print(f"{C_CYAN}{EMOJI_INFO} Original target views: {target_total_views}. Overall success rate: {success_rate:.2f}%{C_END}")
    if total_tasks_processed_or_attempted == 0 and target_total_views > 0:
        print(f"{C_YELLOW}{EMOJI_WARNING} No view attempts recorded. Check logs.{C_END}")
    elif total_tasks_processed_or_attempted == 0 and target_total_views == 0:
         print(f"{C_YELLOW}{EMOJI_INFO} No views targeted or processed.{C_END}")

    # 9. Cleanup Managed Tor Instances
    print(f"\\n{C_BLUE}{EMOJI_GEAR} Cleaning up managed Tor instances...{C_END}")
    if pytor and managed_tor_instances_details:
        pytor.cleanup_tor_instances(managed_tor_instances_details)
        print(f"{C_GREEN}{EMOJI_SUCCESS} Managed Tor instances cleanup initiated.{C_END}")
    elif not managed_tor_instances_details:
        print(f"{C_CYAN}{EMOJI_INFO} No user-space Tor instances started by this script.{C_END}")
    else:
        print(f"{C_WARNING}{EMOJI_WARNING} Pytor unavailable, cannot clean Tor instances: {managed_tor_instances_details}{C_END}")

    print(f"\\n{C_HEADER}{EMOJI_THANKS} Thanks for using KADDU YT-VIEWS! {EMOJI_STAR}{C_END}")
    print(f"{C_YELLOW}Consider starring: https://github.com/Kaddu-Hacker/InfiniteYtViews{C_END}")
    print(f"{C_CYAN}{EMOJI_INFO} [Infotainment] {get_random_infotainment()}{C_END}")

    # --- TASK.md and Changelog update logic ---
    def mark_task_completed(task_desc):
        """Mark the current task as completed in TASK.md and log in Changelog if those files exist."""
        import datetime
        today = datetime.date.today().isoformat()
        # Update TASK.md
        if os.path.exists("TASK.md"):
            with open("TASK.md", "a", encoding="utf-8") as f:
                f.write(f"\n- [x] {task_desc} (completed {today})\n")
        # Update Changelog
        if os.path.exists("Changelog"):
            with open("Changelog", "a", encoding="utf-8") as f:
                f.write(f"\n[{today}] {task_desc} completed and script finalized.\n")

    mark_task_completed("Finalize, robustify, and automate main.py for user-friendly, non-manual operation")


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\\n\\n{C_WARNING}{EMOJI_WARNING} Keyboard interrupt! Signaling stop...{C_END}")
        stop_event_global.set()
        print(f"{C_BLUE}Please wait for graceful shutdown...{C_END}")
        time.sleep(5) 
    except SystemExit as e:
        if e.code != 0:
            print(f"{C_FAIL}{EMOJI_FAIL} Script exited (Code: {e.code}).{C_END}")
    except Exception as e_critical:
        print(f"\\n{C_FAIL}{EMOJI_ERROR}{C_BOLD} --- CRITICAL UNEXPECTED ERROR --- {C_END}")
        print(f"{C_FAIL}Type: {type(e_critical).__name__}, Details: {e_critical}{C_END}")
        import traceback
        print(f"{C_GRAY}--- Traceback --- \\n{traceback.format_exc()}--- End Traceback ---{C_END}")
        print(f"{C_CYAN}Report this issue on GitHub with the traceback.{C_END}")
    finally:
        print(C_END) 
        print(f"{C_BLUE}{EMOJI_INFO} KADDU YT-VIEWS program finished.{C_END}")

# Make sure re is imported if used for video ID extraction (added to main)
import re
