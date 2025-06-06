import path from 'path';
import fs from 'fs';
import { logInfo, logError, logSuccess, createSpinner } from './ui.js';
import inquirer from 'inquirer';
import { spawnSync } from 'child_process';

// Robust dynamic import for selenium-webdriver with auto-install
let Builder, By, until, chrome, firefox;
async function loadSelenium() {
  try {
    const selenium = await import('selenium-webdriver');
    Builder = selenium.Builder;
    By = selenium.By;
    until = selenium.until;
    chrome = (await import('selenium-webdriver/chrome.js')).default;
    firefox = (await import('selenium-webdriver/firefox.js')).default;
  } catch (e) {
    console.error('[ERROR] Selenium backend selected but selenium-webdriver is not installed.');
    const { install } = await inquirer.prompt([{
      type: 'confirm',
      name: 'install',
      message: 'Install selenium-webdriver now?',
      default: true,
    }]);
    if (install) {
      const result = spawnSync('npm', ['install', 'selenium-webdriver'], { stdio: 'inherit' });
      if (result.status === 0) {
        // Try import again
        return await loadSelenium();
      } else {
        console.error('[ERROR] Failed to install selenium-webdriver. Please install it manually.');
        process.exit(1);
      }
    } else {
      console.error('[ERROR] selenium-webdriver is required. Exiting.');
      process.exit(1);
    }
  }
}
await loadSelenium();

// Helper to load config/paths.json for Selenium driver path
function getSeleniumDriverPath() {
  try {
    const configPath = path.resolve('config/paths.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return config.seleniumDriverPath || null;
    }
  } catch (e) {}
  return null;
}

/**
 * Launches a Selenium WebDriver instance for Chrome or Firefox.
 * @param {object} options - Browser launch options.
 * @param {boolean} options.headless - Whether to run in headless mode.
 * @param {string|null} options.proxy - Proxy string (e.g., socks5://host:port or http://host:port).
 * @param {boolean} options.debug - Enable debug logging.
 * @param {string} options.browserType - 'chrome' or 'firefox'.
 * @returns {Promise<{driver: import('selenium-webdriver').WebDriver, page: any}|null>}
 */
export async function launchSeleniumBrowser({ headless = true, proxy = null, debug = false, browserType = 'chrome' }) {
  const spinner = createSpinner('Launching Selenium browser...');
  spinner.start();
  try {
    let builder = new Builder().forBrowser(browserType);
    const driverPath = getSeleniumDriverPath();
    if (browserType === 'chrome') {
      const options = new chrome.Options();
      if (headless) options.headless();
      if (proxy) options.addArguments(`--proxy-server=${proxy}`);
      if (driverPath) builder.setChromeService(new chrome.ServiceBuilder(driverPath));
      builder.setChromeOptions(options);
    } else if (browserType === 'firefox') {
      const options = new firefox.Options();
      if (headless) options.headless();
      if (proxy) options.setPreference('network.proxy.type', 1);
      // Note: For SOCKS proxy, set more prefs if needed
      if (driverPath) builder.setFirefoxService(new firefox.ServiceBuilder(driverPath));
      builder.setFirefoxOptions(options);
    }
    const driver = await builder.build();
    spinner.succeed('Selenium browser launched successfully.');
    return { driver, page: driver }; // For compatibility with Puppeteer code
  } catch (error) {
    spinner.fail('Failed to launch Selenium browser.');
    logError(`Error launching Selenium browser: ${error.message}`);
    if (debug && error.stack) {
      logError(error.stack);
    }
    return null;
  }
} 