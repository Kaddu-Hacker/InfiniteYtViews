import { Command } from 'commander';
import inquirer from 'inquirer';
import chalk from 'chalk';
import figlet from 'figlet';
import {
  showBanner,
  createSpinner,
  logSuccess,
  logError,
  logInfo,
  logDebug,
  logWarning,
  showCustomBanner,
  setLogLevel,
} from '../lib/ui.js';
import {
  validateYouTubeUrl,
  delay,
  getRandomDelay,
} from '../lib/utils.js';
import {
  initializeAudio,
  playStartupSound,
  playSuccessSound,
  playErrorSound,
  playCompletionSound,
  setAudioEnabled,
  getAudioStats
} from '../lib/audio.js';
import * as actions from '../lib/actions.js';
import * as tor from '../lib/tor.js';
import * as proxyPool from '../lib/proxyPool.js';
import * as browser from '../lib/browser.js';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import { promisify } from 'util';
import fs from 'fs';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);

const program = new Command();

// CLI Configuration - Simplified, most settings will be prompted interactively
program
  .name('yt-views-gen-interactive')
  .description('Interactive YouTube Views Generator with Tor/Proxy IP rotation and human-like behavior')
  .version('2.0.0')
  .option('-u, --url <url>', 'YouTube video URL (can be prompted if omitted)')
  .option('-n, --views <number>', 'Number of views (can be prompted if omitted)', (val) => parseInt(val))
  .option('--headless', 'Run browser in headless mode without prompting')
  .option('--no-headless', 'Run browser in non-headless mode (visible) without prompting')
  .option('--like-video', 'Attempt to like the video without prompting for this choice')
  .option('--debug', 'Enable debug mode (sets log level to debug)', false)
  .option('--no-sound', 'Disable sound effects', false)
  .parse(process.argv);

// Promisify figlet.text for async/await usage
const figletAsync = promisify(figlet.text);

// Helper to load backend from config/paths.json
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

async function main() {
  const cliOpts = program.opts();

  // Set log level based on debug flag immediately
  if (cliOpts.debug) {
    setLogLevel('debug');
    logDebug('Debug mode enabled via CLI flag.');
  }

  // Initialize audio system FIRST, based on CLI flag, then allow user to override
  setAudioEnabled(!cliOpts.noSound);
  await initializeAudio();

  // Show a big 'KAADDU' banner above the main banner using figlet and chalk
  const kaaduBanner = await figletAsync('KAADDU', { font: 'ANSI Shadow' });
  console.log('\n' + chalk.red(kaaduBanner) + '\n');
  const ytBanner = await figletAsync('YT Views Gen', 'Slant');
  console.log(chalk.cyan(ytBanner));
  await showBanner('YT Views Gen', 'Slant');
  if (!cliOpts.noSound) {
  }

  logInfo(chalk.blue('Welcome to Interactive YouTube Views Generator v2.0.0'));
  logInfo(chalk.blue('Please answer the following questions to configure your session:\n'));

  const questions = [
    {
      type: 'list',
      name: 'contentType',
      message: chalk.cyanBright('➡️ What type of YouTube content do you want to view?'),
      choices: [
        { name: chalk.green('Video (regular YouTube video)'), value: 'video' },
        { name: chalk.yellow('Shorts (YouTube Shorts)'), value: 'shorts' }
      ],
      default: 'video',
    },
    {
      type: 'input',
      name: 'videoUrl',
      message: chalk.cyanBright('➡️ Enter the YouTube video URL:'),
      default: cliOpts.url, // Use CLI option as default if provided
      validate: (input, answers) => {
        // Fix: answers may be undefined or missing contentType if prompt order or CLI input skips previous questions
        if (!validateYouTubeUrl(input)) return chalk.red('❌ Please enter a valid YouTube URL.');
        if (answers && typeof answers === 'object') {
          if (answers.contentType === 'shorts' && !/\/shorts\//.test(input)) return chalk.red('❌ This is not a Shorts URL.');
          if (answers.contentType === 'video' && /\/shorts\//.test(input)) return chalk.red('❌ This is a Shorts URL, not a regular video.');
        }
        return true;
      },
      when: !cliOpts.url || !validateYouTubeUrl(cliOpts.url), // Ask if not provided or invalid
    },
    {
      type: 'number',
      name: 'numViews',
      message: chalk.cyanBright('➡️ How many views to generate?'),
      default: cliOpts.views || 10,
      validate: (input) => (Number.isInteger(input) && input > 0 && input <= 1000) || chalk.red('❌ Please enter a whole number between 1 and 1000.'),
      when: !cliOpts.views || !(Number.isInteger(cliOpts.views) && cliOpts.views > 0 && cliOpts.views <= 1000),
      filter: Number,
    },
    {
      type: 'number',
      name: 'minWatchSeconds',
      message: chalk.cyanBright('➡️ Minimum watch time per view (seconds):'),
      default: 30,
      validate: (input) => (input >= 10 && input <= 600) || chalk.red('❌ Enter a value between 10 and 600.'),
      filter: Number,
    },
    {
      type: 'number',
      name: 'maxWatchSeconds',
      message: chalk.cyanBright('➡️ Maximum watch time per view (seconds):'),
      default: 60,
      validate: (input, answers) => {
        // Defensive: answers may be undefined or missing minWatchSeconds
        let minWatch = 30; // fallback default
        if (answers && typeof answers === 'object' && typeof answers.minWatchSeconds === 'number') {
          minWatch = answers.minWatchSeconds;
        } else {
          // fallback to the default in the question definition if available
          const minQ = questions.find(q => q.name === 'minWatchSeconds');
          if (minQ && typeof minQ.default === 'number') minWatch = minQ.default;
        }
        return (input >= minWatch && input <= 700) || chalk.red(`❌ Must be >= min watch time (${minWatch}s) and <= 700.`);
      },
      filter: Number,
    },
    {
      type: 'list',
      name: 'proxyMode',
      message: chalk.cyanBright('➡️ Select proxy mode:'),
      choices: [
        { name: chalk.green('Tor (recommended, requires Tor service running)'), value: 'tor' },
        { name: chalk.yellow('HTTP Proxies (fetch from public lists)'), value: 'http' },
        // { name: 'None (use your direct IP - not recommended)', value: 'none' } // 'none' mode needs careful implementation
      ],
      default: 'tor',
    },
    // Tor specific questions - appear if proxyMode is 'tor'
    {
      type: 'input',
      name: 'torHost',
      message: chalk.yellow('➡️ Tor SOCKS Host:'),
      default: '127.0.0.1',
      when: (answers) => answers.proxyMode === 'tor',
    },
    {
      type: 'input',
      name: 'torPort',
      message: chalk.yellow('➡️ Tor SOCKS Port:'),
      default: '9050',
      when: (answers) => answers.proxyMode === 'tor',
      validate: input => (!isNaN(parseFloat(input)) && isFinite(input) && Number(input) > 0 && Number(input) < 65536) || chalk.red('❌ Invalid port.'),
      filter: Number,
    },
    {
      type: 'input',
      name: 'torControlHost',
      message: chalk.yellow('➡️ Tor Control Host:'),
      default: '127.0.0.1',
      when: (answers) => answers.proxyMode === 'tor',
    },
    {
      type: 'input',
      name: 'torControlPort',
      message: chalk.yellow('➡️ Tor Control Port:'),
      default: '9051',
      when: (answers) => answers.proxyMode === 'tor',
      validate: input => (!isNaN(parseFloat(input)) && isFinite(input) && Number(input) > 0 && Number(input) < 65536) || chalk.red('❌ Invalid port.'),
      filter: Number,
    },
    {
      type: 'password',
      name: 'torControlPassword',
      message: chalk.yellow('➡️ Tor Control Password (leave blank if none):'),
      mask: '*',
      default: '',
      when: (answers) => answers.proxyMode === 'tor',
    },
    // HTTP Proxy specific questions - appear if proxyMode is 'http'
    {
        type: 'input',
        name: 'customProxyUrls',
        message: chalk.yellow('➡️ Enter comma-separated URLs for HTTP proxy lists (e.g., https://site.com/list.txt,...):'),
        default: 'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt,https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        when: (answers) => answers.proxyMode === 'http',
        filter: (input) => typeof input === 'string' ? input.split(',').map(url => url.trim()).filter(url => url) : [],
        validate: (input) => (Array.isArray(input) && input.every(url => validateYouTubeUrl(url, true) /* Quick check for URL structure */)) || input.length === 0 || chalk.red('❌ Please provide valid comma-separated URLs or leave blank for none initially.'),
    },
    {
      type: 'confirm',
      name: 'runHeadless',
      message: chalk.cyanBright('➡️ Run browser in headless mode (no UI)?'),
      default: true,
      // Ask only if neither --headless nor --no-headless is specified
      when: cliOpts.headless === undefined && cliOpts.noHeadless === undefined,
    },
    {
      type: 'confirm',
      name: 'attemptLikeVideo',
      message: chalk.cyanBright('➡️ Attempt to "like" each video?'),
      default: false,
      when: cliOpts.likeVideo === undefined, // Ask if --like-video flag is not used
    },
    {
      type: 'number',
      name: 'minCycleDelay',
      message: chalk.cyanBright('➡️ Minimum delay between view cycles (seconds):'),
      default: 10,
      validate: (input) => (input >= 5 && input <= 300) || chalk.red('❌ Enter between 5 and 300.'),
      filter: Number,
    },
    {
      type: 'number',
      name: 'maxCycleDelay',
      message: chalk.cyanBright('➡️ Maximum delay between view cycles (seconds):'),
      default: 30,
      validate: (input, answers) => {
        // Defensive: answers may be undefined or missing minCycleDelay
        let minCycle = 10; // fallback default
        if (answers && typeof answers === 'object' && typeof answers.minCycleDelay === 'number') {
          minCycle = answers.minCycleDelay;
        } else {
          // fallback to the default in the question definition if available
          const minQ = questions.find(q => q.name === 'minCycleDelay');
          if (minQ && typeof minQ.default === 'number') minCycle = minQ.default;
        }
        return (input >= minCycle && input <= 600) || chalk.red(`❌ Must be >= min cycle delay (${minCycle}s) and <= 600.`);
      },
      filter: Number,
    },
    {
        type: 'confirm',
        name: 'userEnableSound',
        message: chalk.cyanBright('➡️ Enable sound effects for this session?'),
        default: !cliOpts.noSound, // Default based on --no-sound flag
        when: !cliOpts.noSound, // Only ask if --no-sound is NOT set (i.e., sound could be on)
    }
  ];

  const promptedOptions = await inquirer.prompt(questions);

  // Determine final options, giving precedence to specific CLI flags where appropriate
  const finalOptions = {
    contentType: promptedOptions.contentType,
    videoUrl: cliOpts.url || promptedOptions.videoUrl,
    numViews: cliOpts.views || promptedOptions.numViews,
    minWatchSeconds: promptedOptions.minWatchSeconds,
    maxWatchSeconds: promptedOptions.maxWatchSeconds,
    proxyMode: promptedOptions.proxyMode,
    // Tor/HTTP specific options ARE NOW part of promptedOptions if their 'when' condition was met
    torHost: promptedOptions.torHost, // Will be undefined if not tor mode
    torPort: promptedOptions.torPort,
    torControlHost: promptedOptions.torControlHost,
    torControlPort: promptedOptions.torControlPort,
    torControlPassword: promptedOptions.torControlPassword,
    customProxyUrls: promptedOptions.customProxyUrls, // Will be undefined if not http mode
    headless: cliOpts.headless ? true : (cliOpts.noHeadless ? false : promptedOptions.runHeadless),
    performLike: cliOpts.likeVideo ? true : promptedOptions.attemptLikeVideo,
    minCycleDelay: promptedOptions.minCycleDelay,
    maxCycleDelay: promptedOptions.maxCycleDelay,
    enableSound: cliOpts.noSound ? false : promptedOptions.userEnableSound,
    debug: cliOpts.debug,
  };
  
  // Update audio enabled status based on final decision
  setAudioEnabled(finalOptions.enableSound);
  if (finalOptions.enableSound && main) { // Check main to avoid issues during very early startup/banner
      await playStartupSound(); // Play startup sound after prompts if sound is enabled
  } else if (!finalOptions.enableSound) {
      logInfo(chalk.yellow('Sound effects are disabled for this session.'));
  }

  if (finalOptions.debug) {
    logDebug('CLI Opts Used:', cliOpts);
    logDebug('Prompted Options (includes conditional Tor/HTTP):', promptedOptions);
    logDebug('Final Effective Options:', finalOptions);
  }

  logInfo(chalk.greenBright('\nCore and Network specific configuration complete. Proceeding with application startup...'));
  
  // --- Main Application Logic starts here ---
  let currentProxyString = null;
  let lastIp = null;
  const initSpinner = createSpinner('Initializing network configuration...');
  initSpinner.start();

  // Prepare config objects for modules, derived from finalOptions
  const torConfigForModule = {
    host: finalOptions.torHost,
    port: finalOptions.torPort,
    controlHost: finalOptions.torControlHost,
    controlPort: finalOptions.torControlPort,
    password: finalOptions.torControlPassword,
  };
  
  // For proxyPool, we'll pass sources directly to initProxyPool.
  // Other proxyPool settings like timeout/refresh can be hardcoded or prompted if needed later.
  const proxySourcesForPool = finalOptions.customProxyUrls || [];

  if (finalOptions.proxyMode === 'tor') {
    initSpinner.updateText('Initializing Tor connection...');
    try {
      await tor.initTor(torConfigForModule);
      currentProxyString = `socks5://${finalOptions.torHost}:${finalOptions.torPort}`;
      const ip = await tor.getCurrentIp(torConfigForModule); // Pass config if needed by getCurrentIp
      if (!ip) {
        initSpinner.fail('Failed to connect via Tor or get initial IP. Check Tor setup.');
        process.exit(1);
      }
      initSpinner.succeed(`Tor initialized. Current IP via Tor: ${ip}`);
    } catch (torError) {
      initSpinner.fail(`Tor initialization failed: ${torError.message}`);
      logError('Ensure Tor service is running and accessible as per configuration.');
      process.exit(1);
    }
  } else if (finalOptions.proxyMode === 'http') {
    initSpinner.updateText('Initializing HTTP Proxy Pool...');
    try {
      // Assuming initProxyPool can accept an object with sources, or just the sources array.
      // The lib/proxyPool.js will need to be compatible with this.
      await proxyPool.initProxyPool({ sources: proxySourcesForPool, forceFetch: true });

      const stats = proxyPool.getProxyStats();
      if (stats.workingProxies === 0 && (stats.totalProxies > 0 || proxySourcesForPool.length > 0) ) {
        initSpinner.warn('Proxy pool initialized. Will attempt to fetch/validate on first use or if empty.');
      } else if (stats.workingProxies === 0 && proxySourcesForPool.length === 0) {
        initSpinner.fail('Proxy pool init attempted, but no proxy sources were configured/found.');
        process.exit(1);
      } else {
        initSpinner.succeed(`HTTP Proxy Pool initialized. ${stats.workingProxies}/${stats.totalProxies} working/total (may fetch more).`);
      }
    } catch (proxyError) {
      initSpinner.fail(`HTTP Proxy Pool initialization failed: ${proxyError.message}`);
      process.exit(1);
    }
  } else {
    initSpinner.fail(`Invalid proxy mode selected: ${finalOptions.proxyMode}. Exiting.`);
    process.exit(1);
  }

  // User agents are handled internally by browser.js, no loadUserAgents call here.

  let successCount = 0;
  let failCount = 0;
  const mainSpinner = createSpinner('Starting view generation process...');
  mainSpinner.start();

  try {
    // Prompt for backend if not set in config or via CLI
    let backend = getBackend();
    if (!backend || !['Chromium/Puppeteer', 'Selenium (Chrome/Firefox)'].includes(backend)) {
      const backendPrompt = await inquirer.prompt([{
        type: 'list',
        name: 'backend',
        message: chalk.cyanBright('➡️ Which browser automation backend do you want to use?'),
        choices: ['Chromium/Puppeteer', 'Selenium (Chrome/Firefox)'],
        default: 'Chromium/Puppeteer',
      }]);
      backend = backendPrompt.backend;
    }

    // When launching the browser, pass backend and browserType
    let browserType = 'chrome';
    if (backend === 'Selenium (Chrome/Firefox)') {
      const browserTypePrompt = await inquirer.prompt([{
        type: 'list',
        name: 'browserType',
        message: chalk.cyanBright('➡️ Which browser do you want to use with Selenium?'),
        choices: ['chrome', 'firefox'],
        default: 'chrome',
      }]);
      browserType = browserTypePrompt.browserType;
    }

    for (let i = 0; i < finalOptions.numViews; i++) {
      mainSpinner.updateText(`View ${i + 1}/${finalOptions.numViews} - Preparing...`);
      logInfo(`Starting view ${i + 1} of ${finalOptions.numViews} (${finalOptions.contentType.toUpperCase()})...`);

      // For Tor: Only rotate IP after the previous view (not before the first view)
      if (finalOptions.proxyMode === 'tor') {
        if (i > 0) {
          const ipSpinner = createSpinner('Rotating Tor IP...');
          ipSpinner.start();
          try {
            await tor.rotateIP(torConfigForModule);
            await delay(1000); // Give Tor a moment to build the new circuit
            const newIp = await tor.getCurrentIp(torConfigForModule);
            if (!newIp || newIp === lastIp) {
              ipSpinner.warn('Tor IP did not change or could not be confirmed. Proceeding anyway.');
            } else {
              ipSpinner.succeed(`Rotated Tor IP. New IP: ${newIp}`);
              lastIp = newIp;
            }
          } catch (torError) {
            ipSpinner.fail(`Failed to rotate Tor IP: ${torError.message}`);
            failCount++;
            await delay(getRandomDelay(finalOptions.minCycleDelay * 1000, finalOptions.maxCycleDelay * 1000));
            continue;
          }
        } else {
          // On first view, just get the current IP
          const ipSpinner = createSpinner('Checking current Tor IP...');
          ipSpinner.start();
          try {
            lastIp = await tor.getCurrentIp(torConfigForModule);
            if (!lastIp) {
              ipSpinner.warn('Could not confirm current Tor IP.');
            } else {
              ipSpinner.succeed(`Current Tor IP: ${lastIp}`);
            }
          } catch (ipError) {
            ipSpinner.fail(`Failed to get current Tor IP: ${ipError.message}`);
          }
        }
        currentProxyString = `socks5://${finalOptions.torHost}:${finalOptions.torPort}`;
      } else if (finalOptions.proxyMode === 'http') {
        ipSpinner.updateText(`Getting HTTP Proxy for view ${i + 1}...`);
        currentProxyString = await proxyPool.getNextProxy(); 
        if (!currentProxyString) {
          ipSpinner.fail('No working HTTP proxy available for view.');
          logError('No working HTTP proxy available. Skipping view.');
          failCount++;
          await delay(getRandomDelay(finalOptions.minCycleDelay * 1000, finalOptions.maxCycleDelay * 1000));
          continue;
        }
        ipSpinner.succeed(`Using HTTP proxy: ${currentProxyString}`);
      }

      const browserSpinner = createSpinner(`Launching browser for view ${i + 1}...`);
      browserSpinner.start();
      let page = null;
      let browserInstance = null;

      try {
        const browserLaunchOptions = {
          headless: finalOptions.headless,
          proxy: currentProxyString,
          debug: finalOptions.debug,
          browserType,
        };
        const launched = await browser.launchBrowser(browserLaunchOptions);
        if (!launched || !launched.page) {
          throw new Error('Browser launch returned invalid instance or no page.');
        }
        browserInstance = launched.browser;
        page = launched.page;
        browserSpinner.succeed(`Browser launched successfully for view ${i + 1}.`);

        logInfo(`Preparing to watch video ${i + 1} of ${finalOptions.numViews} for ${finalOptions.videoUrl}`);
        const watchDurationSeconds = Math.floor(Math.random() * (finalOptions.maxWatchSeconds - finalOptions.minWatchSeconds + 1)) + finalOptions.minWatchSeconds;
        logInfo(`Selected watch duration for this view: ${watchDurationSeconds} seconds.`);

        const watched = await actions.watchVideo(page, finalOptions.videoUrl, watchDurationSeconds, {
          debug: finalOptions.debug,
        });

        if (watched) {
          if (finalOptions.performLike) {
            await actions.likeVideo(page);
          }
          logSuccess(`View ${i + 1} completed successfully.`);
          successCount++;
          if (finalOptions.enableSound) await playSuccessSound(successCount);
        } else {
          logWarning(`View ${i + 1} did not complete successfully (watchVideo returned false).`);
          failCount++;
          if (finalOptions.enableSound) await playErrorSound();
        }
      } catch (viewError) {
        logError(`Error during view ${i + 1}: ${viewError.message}`);
        if (finalOptions.debug) console.error(viewError);
        failCount++;
        if (finalOptions.enableSound) await playErrorSound();
        if (browserSpinner.isSpinning) browserSpinner.fail('View failed.'); else logWarning('View failed.');
      } finally {
        mainSpinner.updateText(`View ${i + 1}/${finalOptions.numViews} - Finalizing...`);
         if (browserSpinner.isSpinning) browserSpinner.stop();

        if (browserInstance && typeof browserInstance.close === 'function') {
          const closeSpinner = createSpinner('Closing browser...');
          closeSpinner.start();
          try {
            await browserInstance.close();
            closeSpinner.succeed('Browser closed.');
            logDebug(`Closed browser for view ${i + 1}.`);
          } catch (closeError) {
            closeSpinner.fail('Failed to close browser.');
            logError(`Error closing browser for view ${i+1}: ${closeError.message}`);
          }
        } else {
          logDebug(`Browser instance not available or close method missing for view ${i + 1}.`);
        }
      }

      if (i < finalOptions.numViews - 1) {
        const sleepTime = getRandomDelay(finalOptions.minCycleDelay * 1000, finalOptions.maxCycleDelay * 1000);
        mainSpinner.updateText(`View ${i + 1}/${finalOptions.numViews} - Pausing for ${Math.round(sleepTime/1000)}s...`);
        await delay(sleepTime);
      }
    }
    mainSpinner.succeed('All views processed!');
    if (finalOptions.enableSound && successCount > 0) await playCompletionSound();

  } catch (error) {
    if (mainSpinner.isSpinning) mainSpinner.fail('Main process encountered an error.');
    else logError('Main process encountered an error.');
    logError(`Fatal error: ${error.message}`);
    if (finalOptions.debug) console.error(error);
    if (finalOptions.enableSound) await playErrorSound();
  } finally {
    logInfo('\nExecution Summary:');
    logSuccess(`Successful views: ${successCount}`);
    logError(`Failed views: ${failCount}`);
    const audioStats = getAudioStats();
    if(finalOptions.debug) logDebug(`Audio stats: ${JSON.stringify(audioStats)}`);
    
    if(mainSpinner && typeof mainSpinner.stop === 'function' && mainSpinner.isSpinning) {
        mainSpinner.stop();
    }
    logInfo('Application finished.');
    process.exit(0);
  }
}

// Global error handlers (can remain, ensure they don't rely on old config)
process.on('SIGINT', () => {
  logWarning('\nOperation cancelled by user (SIGINT). Attempting graceful shutdown...');
  process.exit(0);
});
process.on('SIGTERM', () => {
  logWarning('\nOperation terminated (SIGTERM). Attempting graceful shutdown...');
  process.exit(0);
});
process.on('unhandledRejection', (reason, promise) => {
  logError('Unhandled Rejection at:');
  console.error(promise);
  logError(`Reason: ${reason.stack || reason}`);
  process.exit(1);
});
process.on('uncaughtException', (error) => {
  logError('Uncaught Exception:');
  console.error(error);
  process.exit(1);
});

// ESM-compatible check to run main()
if (process.argv[1] === __filename) {
  main().catch(err => {
    logError('Critical error in main execution:');
    if (err && err.stack) {
      logError(err.stack);
    } else {
      logError(String(err));
    }
    process.exit(1);
  });
}
