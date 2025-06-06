import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import yaml from 'js-yaml';
import { logInfo, logError, logSuccess, startSpinner, stopSpinner, logDebug, createSpinner } from './ui.js';
import path from 'path';
import inquirer from 'inquirer';
import { spawnSync } from 'child_process';

puppeteer.use(StealthPlugin());

// Default list of user agents (expanded to 50+ unique, diverse user agents)
// Covers Windows, Mac, Linux, Android, iOS, Chrome, Firefox, Safari, Edge, Opera, and more
const defaultUserAgents = [
  // Windows Chrome
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36',
  // Windows Firefox
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0',
  // Windows Edge
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36 Edg/118.0.5993.70',
  // Windows Opera
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/107.0.5045.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/106.0.4998.70',
  // Mac Chrome
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36',
  // Mac Firefox
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13.3; rv:120.0) Gecko/20100101 Firefox/120.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13.2; rv:119.0) Gecko/20100101 Firefox/119.0',
  // Mac Safari
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15',
  // Mac Edge
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
  // Mac Opera
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/107.0.5045.36',
  // Linux Chrome
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36',
  // Linux Firefox
  'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
  'Mozilla/5.0 (X11; Linux x86_64; rv:119.0) Gecko/20100101 Firefox/119.0',
  // Linux Opera
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/107.0.5045.36',
  // Android Chrome
  'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.134 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 11; SM-G996B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Mobile Safari/537.36',
  // Android Firefox
  'Mozilla/5.0 (Android 13; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0',
  'Mozilla/5.0 (Android 12; Mobile; rv:119.0) Gecko/119.0 Firefox/119.0',
  // Android Samsung Internet
  'Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/120.0.6099.43 Mobile Safari/537.36',
  // iPhone Safari
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
  'Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
  // iPad Safari
  'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  'Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
  // iOS Chrome
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.43 Mobile/15E148 Safari/604.1',
  // iOS Firefox
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/120.0 Mobile/15E148 Safari/605.1.15',
  // iOS Edge
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/120.0.0.0 Mobile/15E148 Safari/605.1.15',
  // iOS Opera
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) OPT/4.2.0 Mobile/15E148 Safari/605.1.15',
  // Misc
  'Mozilla/5.0 (Linux; U; Android 10; en-US; SM-A505F Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.62 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 9; SM-J730G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.99 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 8.0.0; SM-G950F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36',
  'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36',
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

// Helper to load config/paths.json for browserPath
function getBrowserBinaryPath() {
  try {
    const configPath = path.resolve('config/paths.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return config.browserPath || null;
    }
  } catch (e) {}
  return null;
}

// Helper to load config/paths.json for backend
function getBackend() {
  try {
    const configPath = path.resolve('config/paths.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return config.backend || 'Chromium/Puppeteer';
    }
  } catch (e) {}
  return 'Chromium/Puppeteer';
}

async function ensurePuppeteer() {
  try {
    require.resolve('puppeteer-extra');
    require.resolve('puppeteer-extra-plugin-stealth');
    require.resolve('puppeteer');
    return true;
  } catch (e) {
    const { install } = await inquirer.prompt([{
      type: 'confirm',
      name: 'install',
      message: 'Puppeteer and plugins are required but not installed. Install them now?',
      default: true,
    }]);
    if (install) {
      const result = spawnSync('npm', ['install', 'puppeteer', 'puppeteer-extra', 'puppeteer-extra-plugin-stealth'], { stdio: 'inherit' });
      if (result.status === 0) {
        return true;
      } else {
        console.error('[ERROR] Failed to install Puppeteer and plugins. Please install them manually.');
        process.exit(1);
      }
    } else {
      console.error('[ERROR] Puppeteer is required. Exiting.');
      process.exit(1);
    }
  }
}

/**
 * Launches a browser instance using the configured backend (Puppeteer or Selenium).
 * @param {object} options - Browser launch options.
 * @param {boolean} options.headless - Whether to run in headless mode.
 * @param {string|null} options.proxy - Proxy string (e.g., socks5://host:port or http://host:port).
 * @param {boolean} options.debug - Enable debug logging.
 * @returns {Promise<{browser: any, page: any}|null>}
 */
async function launchBrowser({ headless = true, proxy = null, debug = false, browserType = 'chrome' }) {
  let backend = getBackend();
  if (backend === 'Selenium (Chrome/Firefox)') {
    try {
      const { launchSeleniumBrowser } = await import('./selenium.js');
      return await launchSeleniumBrowser({ headless, proxy, debug, browserType });
    } catch (e) {
      logError('Selenium backend failed. Trying Puppeteer as fallback...');
      backend = 'Chromium/Puppeteer';
    }
  }
  if (backend === 'Chromium/Puppeteer') {
    await ensurePuppeteer();
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
        '--disable-speech-api',
        '--disable-background-networking',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-breakpad',
        '--disable-client-side-phishing-detection',
        '--disable-component-update',
        '--disable-default-apps',
        '--disable-dev-shm-usage',
        '--disable-domain-reliability',
        '--disable-extensions',
        '--disable-features=AudioServiceOutOfProcess,IsolateOrigins,site-per-process',
        '--disable-hang-monitor',
        '--disable-ipc-flooding-protection',
        '--disable-notifications',
        '--disable-offer-store-unverified-plugins',
        '--disable-popup-blocking',
        '--disable-print-preview',
        '--disable-prompt-on-repost',
        '--disable-renderer-backgrounding',
        '--disable-sync',
        '--metrics-recording-only',
        '--mute-audio',
        '--no-default-browser-check',
        '--no-first-run',
        '--no-pings',
        '--no-zygote',
        '--password-store=basic',
        '--use-gl=swiftshader',
        '--single-process',
      ];
      if (proxy) {
        launchArgs.push(`--proxy-server=${proxy}`);
        logInfo(`Using proxy: ${proxy}`);
      }
      if (debug) {
        logDebug('Puppeteer launch arguments:', launchArgs);
      }
      // Only set executablePath if not blank
      const browserPath = getBrowserBinaryPath();
      const launchOptions = {
        headless: headless ? 'new' : false,
        args: launchArgs,
        ignoreHTTPSErrors: true,
      };
      if (browserPath) {
        launchOptions.executablePath = browserPath;
      }
      const browser = await puppeteer.launch(launchOptions);
      const page = await browser.newPage();
      await page.setViewport(randomViewport);
      await page.setExtraHTTPHeaders({
        'Accept-Language': 'en-US,en;q=0.9',
      });
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
      // Try Selenium as fallback
      logError('Puppeteer backend failed. Trying Selenium as fallback...');
      try {
        const { launchSeleniumBrowser } = await import('./selenium.js');
        return await launchSeleniumBrowser({ headless, proxy, debug, browserType });
      } catch (e2) {
        logError('Both Puppeteer and Selenium backends failed. Exiting.');
        process.exit(1);
      }
    }
  }
  logError('No valid backend available. Exiting.');
  process.exit(1);
}

// ESM-compliant named exports for all browser methods
export { launchBrowser }; 