# KADDU YT-VIEWS SYSTEM

A robust, automated, and human-like YouTube view generator using Tor proxies. Supports both Dockerized Tor (recommended), system Tor, and Termux (Android) for maximum flexibility.

## Features
- **Automatic Free Proxy IP Rotation:** Uses Tor for all proxying and IP rotation—no need to supply or buy proxy IPs. Works in Docker, system Tor, and Termux.
- **Dockerized or System Tor Proxy Management:** Use Docker Compose for isolated, scalable Tor proxies, or fall back to system Tor if Docker is unavailable.
- **Termux Support:** Works on Android via Termux with Tor installed via `pkg`.
- **Automatic Geckodriver Management:** Ensures Selenium can always find the right driver.
- **Rich CLI Output:** Uses the `rich` library for beautiful, readable terminal output.
- **Parallel View Generation:** Distributes view tasks across multiple Tor proxies for speed and reliability.
- **IP Rotation:** Uses the `stem` library to programmatically rotate Tor identities, with optional control port authentication.
- **Smart Human-like Behavior:** Randomized view durations, start delays, user-agents, scrolling, and play actions.
- **User-Friendly CLI:** Interactive command-line interface with colors, emojis, and helpful prompts.
- **Dry Run Mode:** Preview the actions the script will take without actually generating views.

## Onboarding & Automation

- **Automatic Virtual Environment Creation:** If not running in a venv, the script will prompt to create one (or do so automatically with `--auto`).
- **Automatic Python Dependency Installation:** Installs all required Python packages from `requirements.txt` if missing.
- **Automatic System Package Installation:** If `tor` or `firefox` is missing, the script detects your package manager (`apt`, `dnf`, `yum`, `zypper`, `pacman`, or `pkg` for Termux) and offers to install them.
- **Automatic Service Start:** If Tor is installed but not running, the script will offer to start it (or do so with `--auto`).
- **Automated Geckodriver Download:** The script always ensures the correct geckodriver is available before using Selenium.
- **Onboarding Welcome & Troubleshooting:** On first run, the script prints a friendly onboarding message, explains what it will do, and provides troubleshooting links if anything fails.
- **`--auto` Flag:** Use `--auto` for fully non-interactive onboarding and setup.

## Requirements
- Python 3.8+
- Firefox browser (for Selenium)
- Docker (optional, but recommended for easy scaling)
- Docker Compose (optional, for Docker mode)
- Termux (Android) users: [Termux app](https://f-droid.org/packages/com.termux/) and Tor via `pkg install tor`
- The following Python packages (see `requirements.txt`):
  - selenium
  - rich
  - pyfiglet
  - stem
  - requests[socks]
  - docker

## Setup (updated)

### 1. Run the script (auto-onboarding)
```bash
python main.py
```
- The script will guide you through all setup steps, including venv creation, dependency install, and system package install/start.
- Use `python main.py --auto` for full automation (no prompts).

### 2. (Optional) Manual Setup
- If you prefer, you can manually create a venv, install dependencies, and install/start Tor and Firefox as described in previous sections.

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. (Recommended) Dockerized Tor Proxies
- Edit `docker-compose.yml` to scale up proxies (copy/paste service blocks and increment port numbers).
- Start the proxies:
```bash
docker-compose up -d
```

### 3. (Alternative) System Tor (Linux)
- Start your system Tor service (e.g., `sudo service tor start`).
- To use multiple system Tor instances, configure your `torrc` to listen on multiple SOCKS ports, or run multiple Tor processes on different ports.

### 4. (Alternative) Termux (Android)
- Install [Termux](https://f-droid.org/packages/com.termux/) from F-Droid.
- In Termux, install Tor:
```bash
pkg update && pkg upgrade
pkg install tor
```
- Start Tor in Termux:
```bash
tor &
```
- The default SOCKS port is 9050. The script will auto-detect and use it.

## Usage

### Basic usage (auto-detects Docker, system Tor, or Termux):
```bash
python main.py
```

### Force Docker mode:
```bash
python main.py --use-docker
```

### Force system Tor mode:
```bash
python main.py --no-docker
```

### Use Tor control port authentication:
```bash
python main.py --tor-control-pass your_password
# or set the environment variable
export TOR_CONTROL_PASS=your_password
```

## CLI Flags
- `--use-docker`: Force use of Dockerized Tor proxies (default: auto-detect)
- `--no-docker`: Force use of system Tor only (ignore Docker)
- `--tor-control-pass`: Tor control port password (if set in Docker or system Tor)

## How It Works
- The script checks for Docker and Docker Compose, then starts the Tor proxies using `docker-compose` (if available and not disabled).
- If Docker is not available or disabled, it scans for system Tor SOCKS ports (including Termux on Android).
- Uses the `stem` library to control Tor and rotate IPs as needed, with optional control port authentication.
- Selenium is configured to use the SOCKS proxy for each view worker.
- All output is colorized and user-friendly via `rich`.
- **You never need to supply proxy IPs—the script uses Tor for free, rotating proxy IPs automatically.**

## Scaling Proxies
- **Docker mode:** Add more services to `docker-compose.yml` (e.g., `torproxy4`, `torproxy5`, etc.) with unique host port mappings.
- **System Tor mode:** Start more Tor instances on different ports (edit your `torrc` or run multiple Tor processes).
- **Termux:** By default, only one Tor instance is supported (port 9050), but advanced users can run multiple Tor processes on different ports.

## Troubleshooting
- **Docker not found:** Make sure Docker is installed and your user is in the `docker` group.
- **Tor proxies not starting:** Run `docker-compose ps` to check container status. Use `docker-compose logs` for details.
- **System Tor not found:** Make sure Tor is running and listening on the expected ports.
- **Termux:**
  - Install Tor with `pkg install tor`
  - Start Tor with `tor &`
  - The default SOCKS port is 9050.
- **Geckodriver issues:** The script will attempt to download and configure the correct driver automatically.
- **Permission errors:** On Linux, you may need to run `sudo usermod -aG docker $USER` and log out/in.
- **Selenium errors:** Ensure Firefox is installed and compatible with your geckodriver version.
- **Control port authentication errors:** Make sure the password matches your Tor configuration (see `docker-compose.yml` or your `torrc`).

## Security Note
- The Tor control ports are exposed only to localhost by default. For extra security, set a password in `docker-compose.yml` or your system Tor config, and use `--tor-control-pass` or the `TOR_CONTROL_PASS` environment variable.

## License
MIT