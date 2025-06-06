import inquirer from 'inquirer';
import { execSync, spawnSync } from 'child_process';
import os from 'os';
import fs from 'fs';
import path from 'path';

const CONFIG_PATH = path.resolve('config/paths.json');

async function detectOS() {
  const platform = os.platform();
  if (platform === 'win32') return 'Windows';
  if (platform === 'darwin') return 'macOS';
  if (platform === 'linux') {
    // Check for Android/Termux
    if (fs.existsSync('/data/data/com.termux/files/usr/bin')) return 'Termux';
    return 'Linux';
  }
  return 'Unknown';
}

function saveConfig(config) {
  if (!fs.existsSync('config')) fs.mkdirSync('config');
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
  console.log(`\n[INFO] Saved config to ${CONFIG_PATH}`);
}

function tryCommand(cmd, args, options = {}) {
  try {
    const result = spawnSync(cmd, args, { stdio: 'inherit', ...options });
    return result.status === 0;
  } catch (e) {
    return false;
  }
}

// Helper to check if a node module is installed, and auto-install if missing
async function ensureModuleInstalled(moduleName, installCmd) {
  try {
    require.resolve(moduleName);
    return true;
  } catch (e) {
    const { install } = await inquirer.prompt([{
      type: 'confirm',
      name: 'install',
      message: `Module "${moduleName}" is required but not installed. Install it now?`,
      default: true,
    }]);
    if (install) {
      const result = spawnSync('npm', ['install', ...installCmd.split(' ').slice(2)], { stdio: 'inherit' });
      if (result.status === 0) {
        return true;
      } else {
        console.error(`[ERROR] Failed to install ${moduleName}. Please install it manually.`);
        process.exit(1);
      }
    } else {
      console.error(`[ERROR] ${moduleName} is required. Exiting.`);
      process.exit(1);
    }
  }
}

async function main() {
  const detectedOS = await detectOS();
  const { osChoice } = await inquirer.prompt([{
    type: 'list',
    name: 'osChoice',
    message: 'Which OS are you using?',
    choices: ['Windows', 'Linux', 'macOS', 'Termux'],
    default: detectedOS,
  }]);

  const { backend } = await inquirer.prompt([{
    type: 'list',
    name: 'backend',
    message: 'Which browser automation backend do you want to use?',
    choices: ['Chromium/Puppeteer', 'Selenium (Chrome/Firefox)'],
    default: 'Chromium/Puppeteer',
  }]);

  const { autoInstall } = await inquirer.prompt([{
    type: 'confirm',
    name: 'autoInstall',
    message: 'Do you want to auto-install Tor and browser dependencies?',
    default: true,
  }]);

  let torPath = '';
  let browserPath = '';
  let seleniumDriverPath = '';

  if (autoInstall) {
    // Backend-specific dependency check and auto-install
    if (backend === 'Selenium (Chrome/Firefox)') {
      const seleniumOk = await ensureModuleInstalled('selenium-webdriver', 'npm install selenium-webdriver');
      if (!seleniumOk) {
        // Try Puppeteer as fallback
        const puppeteerOk = await ensureModuleInstalled('puppeteer', 'npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth');
        if (puppeteerOk) {
          backend = 'Chromium/Puppeteer';
          console.log('[INFO] Falling back to Puppeteer backend.');
        } else {
          console.error('[ERROR] Could not install Selenium or Puppeteer. Exiting.');
          process.exit(1);
        }
      }
    } else if (backend === 'Chromium/Puppeteer') {
      const puppeteerOk = await ensureModuleInstalled('puppeteer', 'npm install puppeteer puppeteer-extra puppeteer-extra-plugin-stealth');
      if (!puppeteerOk) {
        // Try Selenium as fallback
        const seleniumOk = await ensureModuleInstalled('selenium-webdriver', 'npm install selenium-webdriver');
        if (seleniumOk) {
          backend = 'Selenium (Chrome/Firefox)';
          console.log('[INFO] Falling back to Selenium backend.');
        } else {
          console.error('[ERROR] Could not install Puppeteer or Selenium. Exiting.');
          process.exit(1);
        }
      }
    }
    // Tor install
    if (osChoice === 'Windows') {
      console.log('[INFO] Please download and install Tor Browser from https://www.torproject.org/download/');
      torPath = 'C:/Program Files/Tor Browser/Browser/TorBrowser/Tor/tor.exe';
    } else if (osChoice === 'Linux') {
      console.log('[INFO] Installing Tor using apt...');
      tryCommand('sudo', ['apt', 'update']);
      tryCommand('sudo', ['apt', 'install', '-y', 'tor']);
      torPath = '/usr/bin/tor';
    } else if (osChoice === 'macOS') {
      console.log('[INFO] Installing Tor using brew...');
      tryCommand('brew', ['install', 'tor']);
      torPath = '/usr/local/bin/tor';
    } else if (osChoice === 'Termux') {
      console.log('[INFO] Installing Tor using pkg...');
      tryCommand('pkg', ['install', '-y', 'tor']);
      torPath = '/data/data/com.termux/files/usr/bin/tor';
    }
    // Browser/driver install for selected backend only
    if (backend === 'Chromium/Puppeteer') {
      if (osChoice === 'Windows') {
        console.log('[INFO] Puppeteer will auto-download Chromium on first run.');
        browserPath = '';
      } else if (osChoice === 'Linux') {
        // On Linux, let Puppeteer use its own Chromium unless user provides a real path
        browserPath = '';
      } else if (osChoice === 'macOS') {
        console.log('[INFO] Installing Chromium using brew...');
        tryCommand('brew', ['install', '--cask', 'chromium']);
        browserPath = '/Applications/Chromium.app/Contents/MacOS/Chromium';
      } else if (osChoice === 'Termux') {
        console.log('[INFO] Installing Chromium using pkg...');
        tryCommand('pkg', ['install', '-y', 'chromium']);
        browserPath = '/data/data/com.termux/files/usr/bin/chromium';
      }
    } else if (backend === 'Selenium (Chrome/Firefox)') {
      // Selenium driver install only
      if (osChoice === 'Windows') {
        console.log('[INFO] Please download ChromeDriver or GeckoDriver for Selenium and provide the path.');
        seleniumDriverPath = '';
      } else if (osChoice === 'Linux') {
        console.log('[INFO] Installing ChromeDriver using apt...');
        tryCommand('sudo', ['apt', 'install', '-y', 'chromedriver']);
        seleniumDriverPath = '/usr/bin/chromedriver';
      } else if (osChoice === 'macOS') {
        console.log('[INFO] Installing ChromeDriver using brew...');
        tryCommand('brew', ['install', '--cask', 'chromedriver']);
        seleniumDriverPath = '/usr/local/bin/chromedriver';
      } else if (osChoice === 'Termux') {
        console.log('[INFO] Please download ChromeDriver for Termux and provide the path.');
        seleniumDriverPath = '';
      }
    }
  } else {
    // Manual path entry
    if (backend === 'Chromium/Puppeteer') {
      const { userBrowserPath } = await inquirer.prompt([{
        type: 'input',
        name: 'userBrowserPath',
        message: 'Enter the full path to your Chromium/Chrome browser binary (leave blank for default):',
        default: '',
      }]);
      browserPath = userBrowserPath;
    } else if (backend === 'Selenium (Chrome/Firefox)') {
      const { userSeleniumPath } = await inquirer.prompt([{
        type: 'input',
        name: 'userSeleniumPath',
        message: 'Enter the full path to your Selenium driver (chromedriver/geckodriver):',
        default: '',
      }]);
      seleniumDriverPath = userSeleniumPath;
    }
    const { userTorPath } = await inquirer.prompt([{
      type: 'input',
      name: 'userTorPath',
      message: 'Enter the full path to your Tor binary (leave blank for default):',
      default: torPath,
    }]);
    torPath = userTorPath;
  }

  // Save config
  const config = {
    os: osChoice,
    backend,
    torPath,
    browserPath,
    seleniumDriverPath,
  };
  saveConfig(config);
  console.log('\n[SETUP COMPLETE] You can now run the main CLI as usual.');
}

main().catch(e => {
  console.error('[SETUP ERROR]', e);
  process.exit(1);
}); 