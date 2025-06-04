const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const yaml = require('js-yaml');
const { logInfo, logError, logSuccess, startSpinner, stopSpinner, logDebug, createSpinner } = require('./ui');

puppeteer.use(StealthPlugin());

// Default list of user agents if YAML loading is removed
const defaultUserAgents = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
  // Add more diverse and recent user agents as needed
];

let userAgents = [...defaultUserAgents]; // Use the default list

// Viewport dimensions (common ones)
const viewports = [
  { width: 1920, height: 1080 },
  { width: 1366, height: 768 },
  { width: 1440, height: 900 },
  { width: 1536, height: 864 },
  { width: 1600, height: 900 },
  { width: 1280, height: 1024 },
  { width: 1280, height: 800 },
];

/**
 * Launches a Puppeteer browser instance with stealth settings and proxy.
 * @param {object} options - Browser launch options.
 * @param {boolean} options.headless - Whether to run in headless mode.
 * @param {string|null} options.proxy - Proxy string (e.g., socks5://host:port or http://host:port).
 * @param {boolean} options.debug - Enable debug logging.
 * @returns {Promise<{browser: import('puppeteer').Browser, page: import('puppeteer').Page}|null>}
 */
async function launchBrowser({ headless = true, proxy = null, debug = false }) {
  const spinner = createSpinner('Launching browser...');
  spinner.start();

  try {
    const randomUserAgent = userAgents[Math.floor(Math.random() * userAgents.length)];
    const randomViewport = viewports[Math.floor(Math.random() * viewports.length)];

    logInfo(`Using User-Agent: ${randomUserAgent}`);
    logInfo(`Using Viewport: ${randomViewport.width}x${randomViewport.height}`);

    const launchArgs = [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-infobars',
      '--window-position=0,0',
      '--ignore-certifcate-errors',
      '--ignore-certifcate-errors-spki-list',
      `--user-agent=${randomUserAgent}`,
      '--disable-speech-api', // Disable speech recognition API
      '--disable-background-networking', // Disable various background network services
      '--disable-background-timer-throttling', // Disable timers throttling for background pages
      '--disable-backgrounding-occluded-windows',
      '--disable-breakpad', // Disable crash reporter
      '--disable-client-side-phishing-detection',
      '--disable-component-update',
      '--disable-default-apps',
      '--disable-dev-shm-usage', // Issues in Docker, good to have
      '--disable-domain-reliability',
      '--disable-extensions', // Disable extensions
      '--disable-features=AudioServiceOutOfProcess,IsolateOrigins,site-per-process',
      '--disable-hang-monitor',
      '--disable-ipc-flooding-protection',
      '--disable-notifications',
      '--disable-offer-store-unverified-plugins',
      '--disable-popup-blocking',
      '--disable-print-preview',
      '--disable-prompt-on-repost',
      '--disable-renderer-backgrounding',
      '--disable-sync', // Disable Google sync
      '--metrics-recording-only',
      '--mute-audio', // Mute audio output
      '--no-default-browser-check',
      '--no-first-run',
      '--no-pings', // Don't send pings
      '--no-zygote', // Useful for some environments
      '--password-store=basic', // Avoid gnome-keyring or kwallet
      '--use-gl=swiftshader', // Software renderer to avoid GPU issues
      '--single-process', // May be useful in constrained environments, but can also be less stable
      // Stealth plugin might add more, these are common ones for robustness/stealth
    ];

    if (proxy) {
      launchArgs.push(`--proxy-server=${proxy}`);
      logInfo(`Using proxy: ${proxy}`);
    }

    if (debug) {
        logDebug('Puppeteer launch arguments:', launchArgs);
    }

    const browser = await puppeteer.launch({
      headless: headless ? 'new' : false, // 'new' headless mode is recommended
      args: launchArgs,
      ignoreHTTPSErrors: true,
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH, // Useful for specific Chrome/Chromium installs
    });

    const page = await browser.newPage();
    await page.setViewport(randomViewport);
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'en-US,en;q=0.9',
    });
    
    // Test stealth capabilities (optional, from puppeteer-extra-plugin-stealth example)
    if (debug) {
        try {
            await page.goto('https://bot.sannysoft.com');
            logDebug('Stealth test page loaded. Check results manually if browser is visible.');
            await page.screenshot({ path: 'stealth-test-results.png' });
            logInfo('Stealth test screenshot saved to stealth-test-results.png');
        } catch (stealthTestError) {
            logWarning(`Stealth test page (bot.sannysoft.com) failed to load: ${stealthTestError.message}`);
        }
    }

    spinner.succeed('Browser launched successfully.');
    return { browser, page };

  } catch (error) {
    spinner.fail('Failed to launch browser.');
    logError(`Error launching browser: ${error.message}`);
    if (debug && error.stack) {
        logError(error.stack);
    }
    return null;
  }
}

module.exports = {
  launchBrowser,
  // Removed loadUserAgents as it's now internalized
}; 