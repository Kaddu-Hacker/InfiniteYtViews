const { spawn, exec } = require('child_process');
const os = require('os');
// ui.js will be refactored later, for now, we expect logDebug and logError to be available when it is.
// If ui.js is not yet refactored, these might cause issues if called before ui.js provides them in the expected way.
// For now, we will add placeholder functions if ui.js is not ready or structured differently.
let logDebug = (message) => console.log(`[DEBUG] ${message}`);
let logError = (message) => console.error(`[ERROR] ${message}`);

class AudioManager {
  constructor() {
    // Initialize with values from config
    this.isAudioEnabled = true;
    this.platform = os.platform();
    this.soundsPlayed = 0;
    this.lastSoundTime = 0;
    this.soundCooldown = 500;
    this.successFrequency = 800;
    this.errorFrequency = 400;
    // Import logging functions from ui.js dynamically once it's confirmed to be ready
    // This is a common pattern to avoid circular dependencies at module load time,
    // or to ensure a module is fully initialized before its parts are used.
    this.dynamicImportUI();
  }

  async dynamicImportUI() {
    try {
      const ui = require('./ui');
      logDebug = ui.logDebug || logDebug; // Use imported or keep placeholder
      logError = ui.logError || logError;   // Use imported or keep placeholder
    } catch (e) {
      console.error('[AudioManager] Failed to dynamically import ui.js, using placeholder logs.', e);
    }
  }

  async checkAudioAvailability() {
    try {
      switch (this.platform) {
        case 'linux':
          return await this.checkLinuxAudio();
        case 'darwin':
          return await this.checkMacAudio();
        case 'win32':
          return await this.checkWindowsAudio();
        default:
          logDebug(`Unsupported platform for audio: ${this.platform}`);
          return false;
      }
    } catch (error) {
      logDebug(`Audio availability check failed: ${error.message}`);
      return false;
    }
  }

  async checkLinuxAudio() {
    return new Promise((resolve) => {
      exec('which aplay || which paplay || which speaker-test', (error) => resolve(!error));
    });
  }

  async checkMacAudio() {
    return new Promise((resolve) => {
      exec('which afplay || which say', (error) => resolve(!error));
    });
  }

  async checkWindowsAudio() {
    return new Promise((resolve) => {
      exec('where powershell', (error) => resolve(!error));
    });
  }

  async playBeep(frequency = 800, duration = 200) {
    if (!this.isAudioEnabled || !this.canPlaySound()) {
      return;
    }
    try {
      let platformPlayFn;
      switch (this.platform) {
        case 'linux': platformPlayFn = this.playLinuxBeep; break;
        case 'darwin': platformPlayFn = this.playMacBeep; break;
        case 'win32': platformPlayFn = this.playWindowsBeep; break;
        default: platformPlayFn = this.playFallbackBeep;
      }
      await platformPlayFn.call(this, frequency, duration);
      this.soundsPlayed++;
      this.lastSoundTime = Date.now();
      logDebug(`Played beep: ${frequency}Hz for ${duration}ms on ${this.platform}`);
    } catch (error) {
      logDebug(`Sound playback failed on ${this.platform}: ${error.message}`);
    }
  }

  async playLinuxBeep(frequency, duration) {
    return new Promise((resolve, reject) => {
      const commands = [
        `speaker-test -t sine -f ${frequency} -l 1 -s 1`, // Needs specific duration handling if possible
        // The sox commands are more complex and might require sox to be installed.
        // `paplay <(sox -n -p synth ${duration/1000} sine ${frequency})`,
        // `aplay <(sox -n -p synth ${duration/1000} sine ${frequency})`,
        `printf '\x07'` // Bell character fallback
      ];
      let executed = false;
      for (const cmd of commands) {
        try {
          await new Promise((res, rej) => exec(cmd, { timeout: duration + 500 }, (err) => err ? rej(err) : res()));
          executed = true;
          break;
        } catch (e) { /* try next command */ }
      }
      if (executed) resolve(); else reject(new Error('No working audio command found for Linux'));
    });
  }

  async playMacBeep(frequency, duration) {
    // macOS 'afplay' doesn't easily play frequencies. 'say' can make noises.
    // The [console]::beep in PowerShell is specific. For Mac, a simple beep or osascript is common.
    return new Promise((resolve, reject) => {
      exec(`osascript -e "beep"`, (error) => { // Simple system beep
        if (error) return exec(`printf '\x07'`, (err) => err ? reject(err) : resolve());
        resolve();
      });
    });
  }

  async playWindowsBeep(frequency, duration) {
    return new Promise((resolve, reject) => {
      const psCommand = `powershell -Command "[console]::beep(${frequency},${duration})"`;
      exec(psCommand, { timeout: duration + 500 }, (error) => {
        if (error) return exec('echo \x07', (err) => err ? reject(err) : resolve()); // Fallback bell
        resolve();
      });
    });
  }

  async playFallbackBeep() {
    return new Promise((resolve) => {
      process.stdout.write('\x07');
      setTimeout(resolve, 100);
    });
  }

  canPlaySound() {
    return Date.now() - this.lastSoundTime >= this.soundCooldown;
  }

  async playSuccessSound(milestone = 1) {
    if (!this.isAudioEnabled) return;
    logDebug(`Playing success sound, milestone: ${milestone}`);
    const baseFreq = this.successFrequency;
    if (milestone % 10 === 0) {
      await this.playBeep(baseFreq - 200, 150);
      await delay(100);
      await this.playBeep(baseFreq, 150);
      await delay(100);
      await this.playBeep(baseFreq + 200, 200);
    } else if (milestone % 5 === 0) {
      await this.playBeep(baseFreq, 150);
      await delay(100);
      await this.playBeep(baseFreq + 200, 150);
    } else {
      await this.playBeep(baseFreq, 200);
    }
  }

  async playErrorSound() {
    if (!this.isAudioEnabled) return;
    logDebug('Playing error sound');
    await this.playBeep(this.errorFrequency, 300);
    await delay(50);
    await this.playBeep(this.errorFrequency - 100, 200);
  }

  async playCompletionSound() {
    if (!this.isAudioEnabled || !true) return;
    logDebug('Playing completion sound');
    const melody = [
      { freq: 523, dur: 150 }, { freq: 659, dur: 150 },
      { freq: 784, dur: 150 }, { freq: 1047, dur: 300 }
    ];
    for (const note of melody) {
      await this.playBeep(note.freq, note.dur);
      await delay(50);
    }
  }

  async playStartupSound() {
    if (!this.isAudioEnabled || !true) return;
    logDebug('Playing startup sound');
    await this.playBeep(this.successFrequency - 200, 100);
    await delay(50);
    await this.playBeep(this.successFrequency, 100);
  }

  setAudioEnabled(enabled) {
    this.isAudioEnabled = !!enabled;
    logDebug(`Audio ${this.isAudioEnabled ? 'enabled' : 'disabled'}`);
  }

  getStats() {
    return {
      soundsPlayed: this.soundsPlayed,
      audioEnabled: this.isAudioEnabled,
      platform: this.platform,
      lastSoundTime: this.lastSoundTime,
    };
  }

  async initialize() {
    // Called by cli.js before other operations
    await this.dynamicImportUI(); // Ensure UI loggers are loaded
    if (!this.isAudioEnabled) {
      logDebug('Audio is disabled by config.');
      return false;
    }
    const audioAvailable = await this.checkAudioAvailability();
    if (!audioAvailable) {
      logDebug('Audio system check failed or no audio utilities found. Disabling sound effects.');
      this.isAudioEnabled = false;
    } else {
      logDebug(`Audio system initialized for ${this.platform}. Sound effects enabled.`);
    }
    return this.isAudioEnabled;
  }
}

const audioManager = new AudioManager();

// Helper function from utils.js, duplicated here to avoid circular dependency if utils also uses audio.
// Ideally, utils.js should not depend on audio.js.
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  initializeAudio: () => audioManager.initialize(),
  playSuccessSound: (milestone) => audioManager.playSuccessSound(milestone),
  playErrorSound: () => audioManager.playErrorSound(),
  playCompletionSound: () => audioManager.playCompletionSound(),
  playStartupSound: () => audioManager.playStartupSound(),
  setAudioEnabled: (enabled) => audioManager.setAudioEnabled(enabled),
  getAudioStats: () => audioManager.getStats(),
}; 