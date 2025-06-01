# KADDU YT-VIEWS SYSTEM 🎃👀

Automated, Smart, and Human-like YouTube View Simulation!

This script helps simulate views for your YouTube videos and shorts using Tor for IP rotation, with a focus on mimicking human-like behavior. **This script is intended for Linux systems only.**

**GitHub:** [https://github.com/Kaddu-Hacker/InfiniteYtViews](https://github.com/Kaddu-Hacker/InfiniteYtViews)

## 🚀 2025 Update: Smarter Setup & User Experience

- **Automatic Environment Setup:**
  - The script now automatically checks for a Python virtual environment (venv) at startup.
  - If not in a venv, it exits with clear, colorful instructions on how to create and activate one.
  - After venv is detected, it will **automatically install all Python requirements** and **install/start Tor** if needed.
  - All steps show clear, emoji-filled messages for both success and failure, so you always know what is happening and where you might be stuck.
  - If you run as root, the script will warn you and suggest using `sudo -E` to preserve your venv environment variables.
  - Improved venv detection (checks both sys.prefix and VIRTUAL_ENV).

- **Motivational Feedback:**
  - Every step (venv, requirements, Tor install, Tor start) gives a success or failure message with colors and emojis, so you feel motivated and always know what to do next.

- **No More Manual Setup:**
  - Just activate your venv, run the script, and it will handle the rest!


## Features

*   **Smart Human-like Behavior:** Randomized view durations, start delays, and user-agents to appear more organic.
*   **Tor Integration:** Uses Tor for IP rotation, providing anonymity and different IP addresses for views.
*   **Parallel Viewing:** Utilizes multithreading to simulate multiple views concurrently for efficiency.
*   **Link Validation:** Checks if provided YouTube links are accessible via Tor before starting the view process.
*   **User-Friendly CLI:** Interactive command-line interface with colors, emojis, and helpful prompts for Linux terminals.
*   **Video & Shorts Support:** Can process both regular YouTube videos and YouTube Shorts with appropriate watch time considerations.
*   **Customizable:** Set the number of views, parallel connections, and content details.
*   **Dry Run Mode:** Preview the actions the script will take without actually generating views.
*   **System Setup Assistance:** Helps with installing Python dependencies and attempts to manage the Tor service on Linux.
*   **Virtual Environment Guidance:** Prompts users to use a Python virtual environment for better dependency management.
*   **Updated User Agents:** Now uses a list of 50+ real, up-to-date user agent strings for better realism.

## ⚠️ Important Note on Running as Root

This script includes functionality to install system packages (like Tor via `apt`) and manage system services on Linux. Therefore, it **requires `sudo` privileges** for these operations.

**Always be cautious when running scripts with elevated privileges.** It's generally recommended to:
1.  Understand what the script does (review the code).
2.  Run with `sudo` **only** when necessary for specific tasks like initial setup and execution.
3.  Use a virtual environment for Python packages to avoid conflicts with system Python.
4.  If you must use `sudo`, use `sudo -E python3 main.py` to preserve your venv environment variables.

## Setup and Installation (Linux)

It is **STRONGLY RECOMMENDED** to use a Python virtual environment to avoid conflicts with your system's Python packages and to ensure a clean, isolated environment for this script.

**1. Clone the Repository (if you haven't already):**

```bash
# If you have git installed
git clone https://github.com/Kaddu-Hacker/InfiniteYtViews.git
cd InfiniteYtViews
# Otherwise, download the source code and navigate to its directory
```

**2. Create a Python Virtual Environment:**

Open your terminal in the project directory.

*   **On Linux (bash/zsh/etc.):**
    ```bash
    python3 -m venv .venv
    ```
    This will create a folder named `.venv` in your project directory.

**3. Activate the Virtual Environment:**

*   **On Linux (bash/zsh/etc.):**
    ```bash
    source .venv/bin/activate
    ```
    Your terminal prompt should change to indicate that the virtual environment is active (e.g., `(.venv) your-prompt$`).

**4. Run the Script:**

Once the virtual environment is activated, simply run:

```bash
python3 main.py
```

- The script will automatically install all requirements and Tor, and start Tor, if needed.
- If you need to run as root, use:

```bash
sudo -E python3 main.py
```

**You do NOT need to manually install requirements or Tor anymore!**

## Script Workflow

1. **Initial Checks:** Virtual environment, root status.
2. **System Setup:** Installs Python packages from `requirements.txt`. Checks for Tor and attempts to install/start it using system package managers (like `apt`) or the `pytor.py` helper scripts.
3. **User Input:**  
   * Prompts for content type (videos, shorts, or mixed).  
   * For each type, asks for the number of items and an optional default length.  
   * Prompts for individual URLs and their specific lengths (if no default was set).  
   * Asks for the number of views per link and the number of parallel Tor connections.
4. **Tor Status & Link Validation:** Shows the status of Tor connections and validates all provided links via Tor.
5. **Dry Run Option:** Asks if you want to perform a dry run.
6. **View Generation:** If not a dry run, it starts simulating views using a `ThreadPoolExecutor` for parallel processing.  
   * Each view uses a Tor SOCKS port.  
   * Randomized user agents, start delays, and watch times are applied.  
   * Progress is displayed in the console.
7. **Completion:** Shows a summary of views generated and total time taken.

## Important Considerations

*   **YouTube's Terms of Service:** Automating views may be against YouTube's Terms of Service. Use this script responsibly and at your own risk.
*   **Effectiveness:** The actual impact on view counts can vary and may be temporary, as YouTube has sophisticated detection mechanisms.
*   **Resource Usage:** Running many parallel connections can consume system resources and bandwidth. Tor itself adds overhead.
*   **Tor Network:** Be mindful of the Tor network. This tool is for educational and experimental purposes; avoid overloading the network.
*   **SOCKS Dependencies:** If you encounter errors like "Missing dependencies for SOCKS support," ensure `PySocks` is correctly installed in your **activated virtual environment** (`pip install PySocks requests[socks]`).

## Troubleshooting (Linux)

*   **"Missing dependencies for SOCKS support":**  
   * **USE A VIRTUAL ENVIRONMENT!** This is the most common fix.  
   * Activate your venv.  
   * Run `pip install -r requirements.txt` again.  
   * You can also try `pip install PySocks "requests[socks]"` within the venv.
*   **Tor Connection Issues:**  
   * Ensure Tor is installed and the service is running. Use `sudo service tor status` or `systemctl status tor` to check.  
   * Check your firewall settings to ensure Python and Tor can make outbound connections.  
   * If using multiple Tor ports, ensure your Tor configuration (`torrc`) is set up correctly to provide multiple SOCKS listeners (the script currently primarily uses the default 9050 or a sequence starting from it if multiple connections are specified, but `pytor.py` might have its own logic for multiple instances).
*   **Permission Errors (for Tor setup/start):**  
   * The script must be run with `sudo` (e.g., `sudo -E python3 main.py`) for the initial setup steps that install or start the `tor` service and for IP changing operations.

## Disclaimer

This script is provided for educational and experimental purposes only. The developers are not responsible for any misuse or for any actions taken by users of this script. Use at your own risk and discretion.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [G0ldenRat10](https://github.com/G0ldenRat10) for the original PyTor IP Changer
- The Tor Project for providing anonymity services

### 🔗 Original PyTor IP Changer

This project is based in part on [PyTor IP Changer](https://github.com/G0ldenRat10/PyTor-IP-Changer) by G0ldenRat10.

- Rotates your IP address using the Tor network
- Fetches and displays the new IP address
- Retrieves geolocation information (city, region, country) based on the new IP
- Configurable intervals for IP rotation
- Can run in an infinite loop for continuous IP changes

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

- GitHub: [Kaddu-Hacker](https://github.com/Kaddu-Hacker)
- Issues: [Report Issues](https://github.com/Kaddu-Hacker/InfiniteYtViews/issues)

---

<p align="center">
  <b>Made with ❤️ by KADDU</b>
</p>
