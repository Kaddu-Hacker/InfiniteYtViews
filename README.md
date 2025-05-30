# 🚀 KADDU's YT-Views

✨ **For Free** ✨

A powerful tool to generate YouTube views by rotating IP addresses through the Tor network. This project enhances the viewing experience with a beautiful CLI interface and robust IP rotation.

![KADDU's YT-Views]

## ✅ Features

- 🔄 **Advanced IP Rotation** - Automatically changes your IP address using the Tor network
- 👁️ **Multiple Video Support** - Generate views for multiple videos/shorts simultaneously
- 🕵️ **Undetectable User Agents** - Uses 50+ different user agents to appear natural
- 📊 **Detailed Statistics** - Track view generation with beautiful progress bars
- ⏱️ **Smart Timing Algorithms** - Simulates real user behavior with random viewing times
- 🎨 **Beautiful CLI Interface** - Colorful and informative terminal UI
- 🔒 **Privacy Focused** - All traffic routed through the Tor network
- 🌍 **Geolocation Info** - Fetches and displays the new IP address and its geolocation (city, region, country)
- ♾️ **Infinite Loop Option** - Can run in an infinite loop for continuous IP changes

## 📋 Requirements

- 🐧 **Operating System**:
  - Linux-based operating system (Ubuntu, Debian, Fedora, CentOS, Red Hat, or Arch)
- 🐍 **Python 3.6 or higher**
- 🔑 **Root privileges** (required to control the Tor service)

## 📥 Installation

### 🐧 Linux - One-Step Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Kaddu-Hacker/InfiniteYtViews.git
   cd InfiniteYtViews
   ```

2. Run the main script:
   ```bash
   sudo python3 main.py
   ```

That's it! The script will automatically:
- ✅ Install all required Python packages
- ✅ Install Tor if not already present
- ✅ Start the Tor service
- ✅ Configure everything for optimal performance

No manual configuration needed - everything is handled automatically!

## 🔍 How It Works

1. 🔧 **Setup Phase**:
   - Checks for root privileges (required to control the Tor service)
   - Installs required dependencies (Tor, curl, Python packages)
   - Initializes the Tor network and gets an initial IP

2. ⚙️ **Configuration**:
   - Set time interval between IP changes (default: 120 seconds)
   - Specify number of videos/shorts to generate views for
   - Enter URL and desired view count for each video/short

3. 🚀 **View Generation**:
   - Rotates IP addresses through the Tor network at specified intervals
   - Accesses each video URL through the Tor proxy
   - Simulates real user behavior with random viewing times
   - Displays detailed progress with beautiful animations
   - Tracks statistics and provides comprehensive summary

## ⚠️ Important Notes

- 📚 This tool is for **educational purposes only**
- 📜 Using this tool may violate the terms of service of video platforms
- 🔒 IP rotation through Tor may not be sufficient to bypass all detection mechanisms
- 📈 The effectiveness of view generation depends on many factors including the platform's detection algorithms

## 🛠️ Troubleshooting

- If you encounter issues with automatic Tor installation, you can manually install it:
  ```bash
  # For Debian/Ubuntu
  sudo apt-get update && sudo apt-get install -y tor
  
  # For Fedora/CentOS/RHEL
  sudo yum install -y tor
  
  # For Arch Linux
  sudo pacman -S --noconfirm tor
  ```

- If the script fails to fetch IP information:
  1. Check your internet connection
  2. Verify Tor is running with: `sudo systemctl status tor` or `pgrep tor`
  3. Try restarting Tor manually: `sudo systemctl restart tor`
  4. Make sure port 9050 is not blocked by your firewall

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

#### Youtube Tutorial

How to make it work for Firefox or other web browsers, connect to port 9050, enable SOCKS5, code explanation and much more:

[Youtube Video Link](https://www.youtube.com/watch?v=lH5h_PO5hFI&lc=UgylLkXPRhuqQEwbb5h4AaABAg)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Contact

- GitHub: [Kaddu-Hacker](https://github.com/Kaddu-Hacker)
- Issues: [Report Issues](https://github.com/Kaddu-Hacker/InfiniteYtViews/issues)

---

<p align="center">
  <b>Made with ❤️ by KADDU</b>
</p>