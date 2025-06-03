# KADDU YT-VIEWS: Automated YouTube View Generator

**Automate YouTube video views using free Tor proxies. Works on Linux, Docker, and Termux (Android). No proxy lists or paid services needed.**

---

## ✨ Features
- Fully automated YouTube view generation using Tor for free, rotating proxies
- Works on Linux, Docker, and Termux (Android)
- No need for proxy lists or paid services
- Supports both system Tor and Dockerized Tor proxies
- User-friendly onboarding and troubleshooting
- Plug-and-play: script auto-installs/starts dependencies and guides you

---

## 🚀 Quick Start (Universal)

1. **Clone the repository:**
   ```bash
   git clone <your_repo_url>
   cd <repo_folder>
   ```
2. **Create and activate a Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   # On Windows: .venv\Scripts\activate.bat
   ```
3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the script:**
   ```bash
   python main.py
   ```
   - The script will guide you through setup, check for Tor, Docker, and Firefox, and tell you what to do next.

---

## 🐧 Linux (Debian/Ubuntu)

### **Recommended: Docker Mode**
- **Install Docker & Docker Compose:**
  ```bash
  sudo apt update && sudo apt install docker.io docker-compose-plugin -y
  sudo systemctl enable docker --now
  sudo usermod -aG docker $USER  # Log out and back in after this
  ```
- **Run the script:**
  ```bash
  python main.py --use-docker
  ```
  - The script will start multiple Tor proxies using Docker Compose.

### **No Docker? Use System Tor**
- **Install Tor and Firefox:**
  ```bash
  sudo apt update && sudo apt install tor firefox -y
  sudo service tor start
  ```
- **Run the script:**
  ```bash
  python main.py --no-docker
  ```

---

## 🪟 Windows/macOS

- **Install [Docker Desktop](https://www.docker.com/products/docker-desktop)**
- **Start Docker Desktop from your applications menu**
- **Run the script:**
  ```bash
  python main.py --use-docker
  ```
- **If prompted, start Docker Compose services:**
  ```bash
  docker-compose up -d --build
  ```

---

## 📱 Termux (Android)

### **A. System Tor (No Docker, No Root Required)**
1. **Install Python, Tor, and Firefox:**
   ```bash
   pkg update && pkg upgrade -y
   pkg install python tor firefox -y
   ```
2. **Start Tor:**
   ```bash
   tor &
   ```
3. **Create and activate a venv, then run:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   python main.py
   ```

### **B. Docker in Termux (Advanced, With or Without Root)**

> **Note:** Docker does **not** run natively on unrooted Android. You have two main options:
> - **Rooted device:** You can run Docker natively (with kernel patches and root, see below).
> - **Unrooted device:** You can run Docker inside a Linux VM using QEMU or Proot (slower, but works without root).
>
> **⚠️ WARNING:** On Android 12 and newer, or some recent devices, Docker may not work due to kernel/cgroup changes. Before attempting native Docker, run the [Moby check-config.sh script](https://raw.githubusercontent.com/moby/moby/master/contrib/check-config.sh) in Termux to check kernel compatibility:
> ```bash
> pkg install wget tsu
> wget https://raw.githubusercontent.com/moby/moby/master/contrib/check-config.sh
> chmod +x check-config.sh
> sudo ./check-config.sh
> ```
> If you see missing required configs in red, native Docker will likely not work. In that case, use the QEMU/Proot VM method instead.

#### **1. Docker via QEMU/Proot/VM (No Root Required)**
- You can run a full Linux distribution (e.g., Alpine, Ubuntu) inside Termux using QEMU or Proot, and then install Docker inside that VM.
- See these up-to-date guides:
  - [cyberkernelofficial/docker-in-termux (QEMU, no root)](https://github.com/cyberkernelofficial/docker-in-termux)
  - [Slick9000/docker-on-termux (QEMU/Proot, no root)](https://github.com/Slick9000/docker-on-termux)
- **Summary:**
  1. Install QEMU and required packages in Termux:
     ```bash
     pkg update && pkg install qemu-utils qemu-system-x86_64-headless wget -y
     ```
  2. Download a Linux ISO (e.g., Alpine), create a VM, and boot it with QEMU.
  3. Inside the VM, install Docker as you would on a normal Linux system.
  4. Use Docker as usual **inside the VM** (no sudo needed).

#### **2. Native Docker (Rooted Android, Patched Kernel)**
- If your device is rooted and you have a compatible kernel, you can run Docker natively in Termux.
- See this detailed guide: [FreddieOliveira's Gist: Docker on Android (root, kernel patches)](https://gist.github.com/FreddieOliveira/efe850df7ff3951cb62d74bd770dce27)
- **Key points:**
  - You need root access (use `tsu` or `su` in Termux)
  - You may need to patch and recompile your kernel for full Docker support
  - Some features (like overlayfs) may require additional kernel tweaks
  - Once set up, you can run Docker **without sudo** by using a root shell

#### **3. Using Docker Compose in Termux**
- Once Docker is running (inside a VM or natively), you can use `docker-compose` as usual:
  ```bash
  docker-compose up -d --build
  ```
- Then run the script with:
  ```bash
  python main.py --use-docker
  ```

#### **4. Tips for Termux + Docker**
- **No sudo in Termux:** Use `tsu` (if rooted) or run as root shell
- **Unrooted:** Always use QEMU/Proot/VM method
- **Rooted:** Follow the kernel patching guide for best results
- **Performance:** QEMU/Proot is slower than native, but works on any device
- **Troubleshooting:** See the linked guides for common issues and solutions

---

## 🐳 Docker Compose (Manual/Advanced)

- To manually start Tor proxies:
  ```bash
  docker-compose up -d --build
  ```
- Then run the script with:
  ```bash
  python main.py --use-docker
  ```

---

## ⚡ Usage Examples

- **Interactive, auto-detect mode:**
  ```bash
  python main.py
  ```
- **Use Docker, auto-confirm all prompts, and process a video:**
  ```bash
  python main.py --use-docker --auto https://www.youtube.com/watch?v=your_video_id --views-per-link 5
  ```
- **Use system Tor on specific ports:**
  ```bash
  python main.py --no-docker --tor-ports 9050,9052 --parallel-workers 2 https://youtu.be/video1 https://youtu.be/video2
  ```
- **Show all options:**
  ```bash
  python main.py --help
  ```

---

## 📝 What To Do If...

- **Script says to activate your venv:**  
  Run:
  ```bash
  source .venv/bin/activate
  # or on Windows:
  .venv\Scripts\activate.bat
  ```
- **Docker fails to start:**  
  Run:
  ```bash
  docker-compose up -d --build
  python main.py
  ```
- **You want to generate views:**  
  Provide YouTube URLs as arguments:
  ```bash
  python main.py https://www.youtube.com/watch?v=your_video_id
  ```
- **You want advanced options:**  
  Run:
  ```bash
  python main.py --help
  ```

---

## 🛠️ Troubleshooting

- **Missing dependencies?**  
  The script will prompt to install them. If it fails, install manually as above.
- **Docker not running?**  
  Start Docker Desktop or the Docker daemon.
- **Tor not running?**  
  Start Tor with `sudo service tor start` (Linux) or `tor &` (Termux).
  
  **If the script can't connect to Tor:**
  - Make sure Tor is running and listening on the expected port (default: 9050).
  - You can check with:
    ```bash
    netstat -tuln | grep 9050
    # or
    ss -tuln | grep 9050
    ```
  - If not listening, restart Tor and check your configuration.
- **Permission errors?**  
  On Linux, add your user to the `docker` group and log out/in.
- **Geckodriver issues?**  
  The script downloads it automatically. If it fails, download from [Mozilla Releases](https://github.com/mozilla/geckodriver/releases) and place in `drivers/`.
- **Still stuck?**  
  Run with `--auto` for full automation, or check the script's output for next steps.

---

## 💡 Tips

- **No proxy lists needed:** Tor is used for free, automatic IP rotation.
- **The script always tells you what to do next.**
- **For best results, use Docker mode on Linux.**
- **On Termux, always start Tor before running the script.**
- **For Docker in Termux, see the advanced guides above.**

---

## 📜 License

MIT

---

**Disclaimer:**  
This script is for educational purposes only. Automating views on YouTube may violate their Terms of Service. Use responsibly and at your own risk.

> **Note:** If you installed Firefox via Snap or Flatpak (the default on some Ubuntu systems), Selenium/geckodriver may not work due to profile directory access issues. If you encounter problems, uninstall the Snap/Flatpak version and install the official Mozilla Firefox binary from [mozilla.org](https://www.mozilla.org/firefox/new/) or your package manager.
