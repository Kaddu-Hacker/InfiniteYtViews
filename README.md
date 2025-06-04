# 🎥 YouTube Views Generator (Interactive Edition)

A modern Node.js CLI app that generates YouTube views using Puppeteer browser automation, Tor IP rotation, and human-like behavior simulation. **No config files needed—just run and answer prompts!**

[![GitHub Repo](https://img.shields.io/badge/GitHub-InfiniteYtViews-blue?logo=github)](https://github.com/Kaddu-Hacker/InfiniteYtViews/)

## ⚠️ Important Notice

**This tool is for educational and testing purposes only. Use responsibly and in accordance with YouTube's Terms of Service. The authors are not responsible for any misuse of this software.**

## ✨ Features

- 🔄 **IP Rotation**: Automatic IP rotation through Tor or free HTTP proxies
- 🤖 **Human-like Behavior**: Realistic mouse movements, scrolling, and timing patterns
- 🎭 **Stealth Mode**: Advanced anti-detection techniques using Puppeteer stealth plugins
- 📊 **Progress Tracking**: Real-time progress with colored output and spinners
- 🔊 **Sound Effects**: Audio feedback for milestones and completion events
- 🛡️ **Error Handling**: Comprehensive retry mechanisms and error recovery
- ⚡ **Efficient**: Resource management and cleanup
- 🧑‍💻 **Fully Interactive**: All configuration is handled via CLI prompts—no .env or config files required!

## 🚀 Quick Start

### Prerequisites

- **Node.js** ≥ v16
- **npm** or **yarn**
- **Tor** (optional, for IP rotation)
- **Git**

### Installation

```bash
npm install
```

### Usage (Interactive Mode)

```bash
node bin/cli.js
```

You will be guided through:
- YouTube video URL input
- Number of views to generate
- Watch duration configuration
- Proxy mode selection (Tor or HTTP)
- Tor/Proxy settings (if needed)
- Headless/visible browser mode
- Sound effects and more

All prompts use blue lines, arrows, and sensible defaults for a smooth experience (inspired by YoutubeViewBooster).

### Usage (Command Line Flags)

You can also provide options directly:

```bash
node bin/cli.js -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -n 5 --headless --like-video --no-sound
```

## 📱 TERMUX/Android Setup

**You can run this tool on Android using [Termux](https://termux.dev/):**

1. **Install Termux from F-Droid:**
   - [F-Droid Termux Link](https://f-droid.org/packages/com.termux/)
2. **Update and install dependencies:**
   ```bash
   pkg update && pkg upgrade
   pkg install nodejs git python ffmpeg
   pkg install tor
   ```
3. **Clone the repo:**
   ```bash
   git clone https://github.com/Kaddu-Hacker/InfiniteYtViews.git
   cd InfiniteYtViews
   npm install
   ```
4. **Start Tor in a separate Termux session:**
   ```bash
   tor &
   ```
5. **Run the CLI:**
   ```bash
   node bin/cli.js
   ```

**Notes:**
- Puppeteer will use Chromium bundled with the package. If you have issues, install Chromium manually and set the `PUPPETEER_EXECUTABLE_PATH` env variable.
- For sound effects, install `ffmpeg` or `sox` for best compatibility.
- If you get errors about missing libraries, try: `pkg install libnss3 libatk-bridge2.0-0 libgtk-3-0` (or similar, depending on your device).

## 🔊 Sound Effects

- Startup, success, error, and completion sounds
- Can be enabled/disabled via prompt or `--no-sound` flag

## 🏗️ Architecture

- **CLI Interface** (`bin/cli.js`): Interactive prompts and orchestration
- **Browser Manager** (`lib/browser.js`): Puppeteer automation with stealth plugins
- **Tor Manager** (`lib/tor.js`): IP rotation through Tor SOCKS5 proxy
- **Actions** (`lib/actions.js`): YouTube video interaction simulation
- **Proxy Pool** (`lib/proxyPool.js`): Free proxy fetching and validation
- **UI Manager** (`lib/ui.js`): Progress indicators and colored output
- **Utils** (`lib/utils.js`): Utility functions and helpers

## 🛡️ Security & Privacy

- All traffic routed through Tor or proxies (when enabled)
- No data collection or tracking
- Temporary browser profiles
- Automatic cleanup of resources

## 📊 Statistics & Feedback

- Tracks successful vs failed views
- IP rotation statistics
- Browser performance metrics
- Action execution counts
- Success rates and timing

## 🧪 Testing

Run the test suite (if present):

```bash
npm test
```

## 🧑‍💻 No Config Files Needed!

- **No .env, YAML, or config files required or supported.**
- All configuration is handled interactively at startup.
- Just run the CLI and follow the prompts!

## 🛠️ Troubleshooting

- **Chromium/Puppeteer errors:**
  - Try installing missing libraries (see TERMUX section above).
  - Set `PUPPETEER_EXECUTABLE_PATH` if you have a custom Chromium install.
- **Tor not working:**
  - Make sure Tor is running and listening on the correct port (default 9050).
  - Check your firewall or VPN settings.
- **Proxy pool empty:**
  - Check your internet connection and proxy source URLs.
- **Sound not working:**
  - Install `ffmpeg`, `sox`, or ensure your system supports audio playback from the terminal.

---

> ⚠️ *Use responsibly & ethically. This tool is for research/testing only.* 