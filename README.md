# KADDU YT-VIEWS: Automated YouTube View Generator

**Automate YouTube video views using free Tor proxies. Works on Linux, Docker, and Termux (Android). No proxy lists or paid services needed.**

---

## 🖼️ Banner

```
(When you run the script, you'll see a cool ASCII banner from the ASCII file!)
```

---

## 🚀 Quick Start (All Platforms)

1. **Clone the repository:**
   ```bash
   git clone <your_repo_url>
   cd <repo_folder>
   ```

2. **Create and activate a Python virtual environment:**
   - **Linux/macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - **Windows:**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate.bat
     ```
   - **Termux (Android):**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
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

## 🐧 Linux/Debian

### **Recommended: Docker Mode**
- **Install Docker & Docker Compose:**
  ```bash
  sudo apt update && sudo apt install docker.io docker-compose -y
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

## 📱 Termux (Android)

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

---

## 📜 License

MIT

---

**Disclaimer:**  
This script is for educational purposes only. Automating views on YouTube may violate their Terms of Service. Use responsibly and at your own risk.
