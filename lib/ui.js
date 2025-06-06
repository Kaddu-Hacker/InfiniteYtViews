import chalk from 'chalk';
import ora from 'ora';
import figlet from 'figlet';
import { promisify } from 'util';

const figletAsync = promisify(figlet.text); // figlet.text is the function for generating text

class UIManager {
  constructor() {
    this.spinners = new Map();
  }

  async showBanner(text = 'YT Views Gen', font = 'Standard') {
    try {
      // Use a default font like 'Standard' or 'Slant' if YoutubeViewBooster's font 'ANSI Shadow' is not always available
      // or choose one from figlet.fontsSync()
      const availableFonts = figlet.fontsSync();
      const selectedFont = availableFonts.includes(font) ? font : (availableFonts.includes('Slant') ? 'Slant' : 'Standard');

      const banner = await figletAsync(text, {
        font: selectedFont,
        horizontalLayout: 'default',
        verticalLayout: 'default'
      });
      console.log(chalk.cyan(banner));
      console.log(chalk.gray('-'.repeat(process.stdout.columns || 60))); // Adjust to terminal width
    } catch (error) {
      console.error(`Figlet error: ${error.message}. Using fallback banner.`);
      console.log(chalk.cyan.bold(`\n>> ${text} <<\n`));
      console.log(chalk.gray('-'.repeat(process.stdout.columns || 60)));
    }
  }

  createSpinner(text, options = {}) {
    const spinnerId = Symbol('spinnerId'); // Use Symbol for unique ID
    const oraSpinner = ora({
      text: chalk.yellow(text),
      color: options.color || 'yellow',
      spinner: options.spinner || (process.platform === 'win32' ? 'line' : 'dots'),
      ...options
    });

    this.spinners.set(spinnerId, oraSpinner);

    // Wrap ora methods to manage our collection and add logging
    const originalStart = oraSpinner.start.bind(oraSpinner);
    const originalSucceed = oraSpinner.succeed.bind(oraSpinner);
    const originalFail = oraSpinner.fail.bind(oraSpinner);
    const originalStop = oraSpinner.stop.bind(oraSpinner);
    const originalText = (newText) => { oraSpinner.text = chalk.yellow(newText); }; // ora.text is a setter

    oraSpinner.start = (startText) => {
      if (startText) oraSpinner.text = chalk.yellow(startText);
      this.logDebug(`Spinner started: ${oraSpinner.text}`);
      return originalStart();
    };
    oraSpinner.succeed = (succeedText) => {
      this.spinners.delete(spinnerId);
      if (succeedText) oraSpinner.text = succeedText; // ora.succeed() can take text
      this.logSuccess(oraSpinner.text, true); // true to indicate it's from a spinner
      return originalSucceed(succeedText ? chalk.green(succeedText) : undefined);
    };
    oraSpinner.fail = (failText) => {
      this.spinners.delete(spinnerId);
      if (failText) oraSpinner.text = failText;
      this.logError(oraSpinner.text, true); // true to indicate it's from a spinner
      return originalFail(failText ? chalk.red(failText) : undefined);
    };
    oraSpinner.stop = () => {
      this.spinners.delete(spinnerId);
      this.logDebug(`Spinner stopped: ${oraSpinner.text}`);
      return originalStop();
    };
    oraSpinner.updateText = (newText) => originalText(newText);

    return oraSpinner;
  }

  shouldLog(level) {
    const levels = ['error', 'warn', 'info', 'debug'];
    const currentLevelIndex = levels.indexOf(this.logLevel);
    const messageLevelIndex = levels.indexOf(level);
    return messageLevelIndex <= currentLevelIndex;
  }

  log(message, level = 'info', fromSpinner = false) {
    if (!this.shouldLog(level) && level !== 'error') return; // Always log errors

    let prefix = '';
    let color = chalk.white;

    switch (level) {
      case 'debug':
        prefix = chalk.gray('[DBG]');
        color = chalk.gray;
        break;
      case 'info':
        prefix = chalk.blue('[INF]');
        color = chalk.white;
        break;
      case 'warn':
        prefix = chalk.yellow('[WRN]');
        color = chalk.yellow;
        break;
      case 'error':
        prefix = chalk.red('[ERR]');
        color = chalk.red;
        break;
      default:
        prefix = '[LOG]';
    }
    // If the message is from a spinner success/fail, it might already be colored by ora.
    // For direct logs, apply color.
    const formattedMessage = fromSpinner ? message : color(message);
    console.log(`${prefix} ${formattedMessage}`);
  }

  logInfo(message, fromSpinner = false) {
    this.log(message, 'info', fromSpinner);
  }

  logError(message, fromSpinner = false) {
    this.log(message, 'error', fromSpinner);
  }

  logSuccess(message, fromSpinner = false) { // Success is like info but green
    if (!this.shouldLog('info')) return;
    const prefix = chalk.green('[OK✓]');
    const formattedMessage = fromSpinner ? message : chalk.green(message);
    console.log(`${prefix} ${formattedMessage}`);
  }

  logWarning(message, fromSpinner = false) {
    this.log(message, 'warn', fromSpinner);
  }

  logDebug(message, fromSpinner = false) {
    this.log(message, 'debug', fromSpinner);
  }

  // Table display
  displayTable(data, headers = []) {
    if (!Array.isArray(data) || data.length === 0) {
      this.logWarning('No data to display');
      return;
    }
    if (headers.length === 0 && typeof data[0] === 'object') {
      headers = Object.keys(data[0]);
    }
    const widths = headers.map(header => {
      const dataWidth = Math.max(...data.map(row => String(row[header] || '').length));
      return Math.max(header.length, dataWidth, 10);
    });
    const headerRow = headers.map((header, i) => chalk.bold(header.padEnd(widths[i]))).join(' │ ');
    console.log('┌' + widths.map(w => '─'.repeat(w + 2)).join('┬') + '┐');
    console.log(`│ ${headerRow} │`);
    console.log('├' + widths.map(w => '─'.repeat(w + 2)).join('┼') + '┤');
    data.forEach(row => {
      const dataRow = headers.map((header, i) => String(row[header] || '').padEnd(widths[i])).join(' │ ');
      console.log(`│ ${dataRow} │`);
    });
    console.log('└' + widths.map(w => '─'.repeat(w + 2)).join('┴') + '┘');
  }

  // Statistics display
  displayStats(stats) {
    console.log(chalk.bold('\n📊 Statistics:'));
    console.log(chalk.gray('─'.repeat(20)));
    Object.entries(stats).forEach(([key, value]) => {
      const formattedKey = key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
      const formattedValue = typeof value === 'number' ? value.toLocaleString() : String(value);
      console.log(`${chalk.cyan(formattedKey)}: ${chalk.white(formattedValue)}`);
    });
    console.log();
  }

  // Audio status display
  displayAudioStatus(audioStats) {
    if (audioStats.audioEnabled) {
      console.log(chalk.green('🔊 Audio effects enabled'));
      if (audioStats.soundsPlayed > 0) {
        console.log(chalk.gray(`   Sounds played: ${audioStats.soundsPlayed}`));
      }
    } else {
      console.log(chalk.gray('🔇 Audio effects disabled'));
    }
  }

  // Progress bar
  createProgressBar(total, options = {}) {
    let current = 0;
    const barLength = options.barLength || 30;
    const showPercentage = options.showPercentage !== false;
    const showNumbers = options.showNumbers !== false;
    const update = (value) => {
      current = value;
      const percentage = Math.round((current / total) * 100);
      const filled = Math.round((current / total) * barLength);
      const empty = barLength - filled;
      const bar = '█'.repeat(filled) + '░'.repeat(empty);
      let display = `[${chalk.cyan(bar)}]`;
      if (showPercentage) {
        display += ` ${chalk.bold(percentage)}%`;
      }
      if (showNumbers) {
        display += ` (${current}/${total})`;
      }
      process.stdout.write('\r' + display);
    };
    const complete = () => {
      process.stdout.write('\n');
    };
    return { update, complete };
  }

  // Loading animation
  async showLoading(message, duration = 3000) {
    const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
    let frameIndex = 0;
    const interval = setInterval(() => {
      process.stdout.write(`\r${chalk.cyan(frames[frameIndex])} ${message}`);
      frameIndex = (frameIndex + 1) % frames.length;
    }, 100);
    setTimeout(() => {
      clearInterval(interval);
      process.stdout.write('\r' + ' '.repeat(message.length + 2) + '\r');
    }, duration);
  }

  // Confirmation prompt (stub, to be replaced by inquirer in CLI)
  async confirm(message, defaultValue = false) {
    // This is a stub. Use inquirer in CLI for real prompts.
    return defaultValue;
  }

  // Add section header with emoji and color
  sectionHeader(title, emoji = '🔷') {
    const line = chalk.blueBright('─'.repeat(process.stdout.columns || 60));
    console.log(`\n${line}`);
    console.log(chalk.bold.blueBright(`${emoji}  ${title.toUpperCase()}  ${emoji}`));
    console.log(line);
  }

  // Add summary display for end-of-run
  summary(stats, emoji = '✅') {
    this.sectionHeader('Summary', emoji);
    this.displayStats(stats);
  }

  // Overwrite clear to do a true refresh
  clear() {
    process.stdout.write('\x1Bc');
    // Optionally, print a faint line or logo after clear
    // console.log(chalk.gray('─'.repeat(process.stdout.columns || 60)));
  }

  // Placeholder for other UI methods from YoutubeViewBooster if needed later
  // displayTable, displayStats, displayAudioStatus, showLoading, confirm, clear, etc.

  stopAllSpinners() {
    this.spinners.forEach((spinner, id) => {
      spinner.stop(); // Use original stop if our wrapper causes issues.
      this.spinners.delete(id);
    });
    if (this.spinners.size > 0) {
        this.logDebug('Stopped all active spinners.');
        this.spinners.clear();
    }
  }

  setLogLevel(level) {
    const validLevels = ['error', 'warn', 'info', 'debug'];
    if (validLevels.includes(level)) {
      this.logLevel = level;
      this.logInfo(`Log level set to: ${level}`);
    } else {
      this.logWarning(`Invalid log level: ${level}. Keeping current: ${this.logLevel}`);
    }
  }

  // Show a custom banner with main and sub text
  async showCustomBanner(main = 'KAADU', sub = 'Yt-Views') {
    try {
      const mainBanner = await figletAsync(main, {
        font: 'ANSI Shadow',
        horizontalLayout: 'fitted',
        verticalLayout: 'fitted'
      });
      const subBanner = await figletAsync(sub, {
        font: 'Slant',
        horizontalLayout: 'fitted',
        verticalLayout: 'fitted'
      });
      console.log(chalk.magentaBright(mainBanner));
      console.log(chalk.cyanBright(subBanner));
      console.log(chalk.gray('─'.repeat(process.stdout.columns || 60)));
    } catch (error) {
      // Fallback if figlet fails
      console.log(chalk.magentaBright.bold(`\n${main}\n`));
      console.log(chalk.cyanBright.bold(`\n${sub}\n`));
      console.log(chalk.gray('─'.repeat(process.stdout.columns || 60)));
    }
  }
}

const uiManager = new UIManager();

// ESM-compliant named exports for all UIManager methods
export const showBanner = (text, font) => uiManager.showBanner(text, font);
export const createSpinner = (text, options) => uiManager.createSpinner(text, options);
export const logInfo = (message, fromSpinner) => uiManager.logInfo(message, fromSpinner);
export const logError = (message, fromSpinner) => uiManager.logError(message, fromSpinner);
export const logSuccess = (message, fromSpinner) => uiManager.logSuccess(message, fromSpinner);
export const logWarning = (message, fromSpinner) => uiManager.logWarning(message, fromSpinner);
export const logDebug = (message, fromSpinner) => uiManager.logDebug(message, fromSpinner);
export const stopAllSpinners = () => uiManager.stopAllSpinners();
export const setLogLevel = (level) => uiManager.setLogLevel(level);
export const displayTable = (data, headers) => uiManager.displayTable(data, headers);
export const displayStats = (stats) => uiManager.displayStats(stats);
export const displayAudioStatus = (audioStats) => uiManager.displayAudioStatus(audioStats);
export const createProgressBar = (total, options) => uiManager.createProgressBar(total, options);
export const showLoading = (message, duration) => uiManager.showLoading(message, duration);
export const confirm = (message, defaultValue) => uiManager.confirm(message, defaultValue);
export const clear = () => uiManager.clear();
export const sectionHeader = (title, emoji) => uiManager.sectionHeader(title, emoji);
export const summary = (stats, emoji) => uiManager.summary(stats, emoji);
export const showCustomBanner = (main, sub) => uiManager.showCustomBanner(main, sub);

// Track the last created spinner for start/stop logic
let lastSpinner = null;

/**
 * Starts a new spinner with the given text and stores it as the last spinner.
 * @param {string} text - The spinner text to display.
 */
export const startSpinner = (text) => {
  if (lastSpinner) {
    lastSpinner.stop(); // Stop any previous spinner
  }
  lastSpinner = uiManager.createSpinner(text);
  lastSpinner.start(text);
};

/**
 * Stops the last started spinner. Optionally marks it as success and shows a message.
 * @param {boolean} success - Whether to mark the spinner as succeeded.
 * @param {string} message - The message to display on stop/success.
 */
export const stopSpinner = (success = true, message = '') => {
  if (lastSpinner) {
    if (success) {
      lastSpinner.succeed(message || undefined);
    } else {
      lastSpinner.stop();
    }
    lastSpinner = null;
  }
};

// Export a failSpinner function for error handling with spinners
/**
 * Fails the current spinner with an error message.
 * This is used to indicate a spinner operation failed.
 * @param {string} message - The error message to display with the spinner.
 */
export const failSpinner = (message) => {
  // For simplicity, create a temporary spinner to show the failure
  // In a more advanced implementation, you could track the current spinner
  const spinner = uiManager.createSpinner(message);
  spinner.fail(message);
}; 