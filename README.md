# YouTube Views Generator (yt-views-gen) v2.0.0

A sophisticated Node.js CLI application that generates YouTube views using Puppeteer browser automation with Tor/Proxy IP rotation and human-like behavior simulation.

## Features

*   **Interactive CLI:** User-friendly prompts for easy configuration of view generation tasks.
*   **YouTube Content Types:** Supports both regular YouTube videos and YouTube Shorts.
*   **IP Rotation:**
    *   **Tor Integration:** Utilizes a running Tor service for SOCKS5 proxy, with automated IP rotation.
    *   **HTTP Proxy Pool:** Fetches and validates proxies from public lists.
*   **Human-like Behavior:**
    *   Randomized watch times within user-defined min/max.
    *   Random delays between view cycles.
    *   Random user-agent rotation.
    *   Random viewport sizing.
    *   Simulated human-like scrolling and mouse movements during video watch.
    *   Optional: Attempt to "like" videos.
*   **Stealth:** Uses `puppeteer-extra` with `puppeteer-extra-plugin-stealth` to avoid bot detection.
*   **Browser Control:** Option to run browser in headless or headful (visible) mode.
*   **Audio Feedback:** Optional sound effects for key events (startup, success, error, completion).
*   **Logging:** Informative console output with different log levels (info, debug, warn, error). Ora spinners for progress indication.
*   **Modular Design:** Code is organized into logical modules for better maintainability.
*   **ESM Based:** Modern JavaScript project structure using ES Modules.

## Prerequisites

1.  **Node.js:** Version `18.0.0` or higher. Download from [nodejs.org](https://nodejs.org/).
2.  **NPM:** Version `8.0.0` or higher (usually comes with Node.js).
3.  **Tor Service:**
    *   A running Tor service is **required** if you intend to use the "Tor" proxy mode.
    *   Ensure Tor is installed and running, and that its SOCKS port (default: `9050`) and Control Port (default: `9051`) are accessible.
    *   Refer to the [Tor Project website](https://www.torproject.org/) for installation instructions.
4.  **Audio Utilities (Optional, for sound effects):**
    *   **Linux:** `aplay` (from `alsa-utils`) or `paplay` (from `pulseaudio-utils`) or `speaker-test`.
        ```bash
        sudo apt update && sudo apt install alsa-utils pulseaudio-utils
        ```
    *   **macOS:** `afplay` (built-in) or `say` (built-in). `osascript` for beeps.
    *   **Windows:** PowerShell `[System.Console]::Beep()` (built-in).
    *   If these are not found, sound effects will be automatically disabled.

## Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/Kaddu-Hacker/InfiniteYtViews.git
    cd InfiniteYtViews
    ```
2.  **Install dependencies:**
    ```bash
    npm install
    ```

## Configuration

The application is configured primarily through interactive prompts when you run it. There is no separate `.env` file required for basic operation.

Key settings you'll be prompted for include:
*   YouTube video URL and content type (video/shorts).
*   Number of views to generate.
*   Minimum and maximum watch times.
*   Proxy mode (Tor or HTTP Proxies).
*   Tor connection details (if Tor mode is selected).
*   HTTP Proxy list URLs (if HTTP mode is selected).
*   Headless browser mode.
*   Whether to attempt "liking" videos.
*   Min/max delays between view cycles.
*   Enabling/disabling sound effects.

## Usage

To start the application, run:

```bash
npm start
```

Alternatively, you can directly execute the CLI script:

```bash
node bin/cli.js
```

Follow the interactive prompts to configure and start the view generation process.

### Key CLI Options

You can override some initial prompts using CLI flags:

*   `-u, --url <url>`: YouTube video URL.
*   `-n, --views <number>`: Number of views to generate.
*   `--headless`: Run browser in headless mode (no UI, skips prompt).
*   `--no-headless`: Run browser in non-headless mode (visible UI, skips prompt).
*   `--like-video`: Attempt to "like" the video (skips prompt for this choice).
*   `--debug`: Enable debug mode (sets log level to debug).
*   `--no-sound`: Disable sound effects (overrides any subsequent prompt to enable sound).

Example:
```bash
node bin/cli.js -u "https://www.youtube.com/watch?v=your_video_id" -n 50 --headless --no-sound
```

## Modules Overview

The project is structured into several modules found in the `lib/` directory:

*   `actions.js`: Handles Puppeteer actions on YouTube pages (watching, liking, scrolling).
*   `audio.js`: Manages audio feedback for different events.
*   `browser.js`: Manages Puppeteer browser launch and configuration.
*   `proxyPool.js`: Handles fetching and managing HTTP/SOCKS proxies from lists.
*   `tor.js`: Manages connection and IP rotation with the Tor service.
*   `ui.js`: Provides UI functionalities like banners, spinners, and formatted logging.
*   `utils.js`: Contains utility functions (URL validation, random delays, etc.).

## Troubleshooting

*   **Tor Connection Issues:**
    *   Ensure the Tor service is running and accessible on the configured SOCKS and Control ports.
    *   Check your firewall settings if connection fails.
    *   Verify Tor control password if you have one set.
*   **Puppeteer Errors:**
    *   `Failed to launch browser`: Ensure all Puppeteer dependencies are correctly installed. Sometimes, additional system libraries might be needed depending on your OS (especially on headless Linux servers). Refer to Puppeteer's documentation.
    *   Setting `PUPPETEER_EXECUTABLE_PATH` environment variable might be needed if you want to use a specific Chrome/Chromium binary.
*   **Proxy Issues:**
    *   Public HTTP proxies can be unreliable. If no working proxies are found, the process may fail for that mode.
*   **Bot Detection:** While `puppeteer-extra-plugin-stealth` is used, YouTube's bot detection can still sometimes flag activity. Human-like settings (longer, more varied watch times and delays) can help.

## License

ISC License. See the `LICENSE` file if one is included, or assume ISC if not explicitly stated. Authored by Kaddu-Hacker & AI Assistant. 