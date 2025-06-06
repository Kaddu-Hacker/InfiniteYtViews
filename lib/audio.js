import { spawn, exec } from 'child_process';
import os from 'os';
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
    this.isPlayingSound = false;
    this.successFrequency = 800;
    this.errorFrequency = 400;
    // Import logging functions from ui.js dynamically once it's confirmed to be ready
    // This is a common pattern to avoid circular dependencies at module load time,
    // or to ensure a module is fully initialized before its parts are used.
    this.dynamicImportUI();
  }

  async dynamicImportUI() {
    try {
      const ui = await import('./ui.js');
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
    if (!this.isAudioEnabled || this.isPlayingSound || (Date.now() - this.lastSoundTime < this.soundCooldown)) {
      if (this.isAudioEnabled && (this.isPlayingSound || (Date.now() - this.lastSoundTime < this.soundCooldown))) {
        logDebug('Sound playback skipped: another sound in progress or cooldown active.');
      }
      return;
    }

    this.isPlayingSound = true;
    this.lastSoundTime = Date.now(); // Set time when starting attempt

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
      logDebug(`Played beep: ${frequency}Hz for ${duration}ms on ${this.platform}`);
    } catch (error) {
      logDebug(`Sound playback failed on ${this.platform}: ${error.message}`);
      // If playback fails, reset lastSoundTime to allow immediate retry if appropriate,
      // or rely on cooldown from previous successful sound. For now, keep lastSoundTime as is.
    } finally {
      this.isPlayingSound = false; // Release the lock
    }
  }

  async playLinuxBeep(frequency, duration) {
    const commands = [
      `speaker-test -t sine -f ${frequency} -l 1 -s 1`, // speaker-test needs duration handling
      `printf '\x07'`
    ];
    // Note: speaker-test -l 1 might play for a longer default duration than specified.
    // Proper duration control with speaker-test is complex. Fallback printf is instant.
    // For simplicity, we are not precisely controlling speaker-test duration here.
    let executed = false;
    let lastError = null;
    for (const cmd of commands) {
      try {
        await new Promise((res, rej) => exec(cmd, { timeout: duration + 500 }, (err) => err ? rej(err) : res()));
        executed = true;
        break;
      } catch (e) {
        lastError = e;
      }
    }
    if (executed) return;
    throw new Error('No working audio command found for Linux' + (lastError ? (': ' + lastError.message) : ''));
  }

  async playMacBeep(frequency, duration) {
    // afplay is for files. 'say' can make noises but not specific frequencies easily.
    // osascript beep is simplest.
    return new Promise((resolve, reject) => {
      exec(`osascript -e "beep"`, (error) => {
        if (error) return exec(`printf '\x07'`, (err) => err ? reject(err) : resolve()); // Fallback bell
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
      process.stdout.write('\x07'); // Standard terminal bell
      setTimeout(resolve, 100); // Give it a moment
    });
  }

  canPlaySound() {
    return !this.isPlayingSound && (Date.now() - this.lastSoundTime >= this.soundCooldown);
  }

  async playSuccessSound(milestone = 1) {
    if (!this.isAudioEnabled) return;
    logDebug(`Playing success sound, milestone: ${milestone}`);
    const baseFreq = this.successFrequency;
    if (milestone % 10 === 0) { // Major milestone
      await this.playBeep(baseFreq - 200, 150); await delay(100);
      await this.playBeep(baseFreq, 150); await delay(100);
      await this.playBeep(baseFreq + 200, 200);
    } else if (milestone % 5 === 0) { // Minor milestone
      await this.playBeep(baseFreq, 150); await delay(100);
      await this.playBeep(baseFreq + 200, 150);
    } else { // Regular success
      await this.playBeep(baseFreq, 200);
    }
  }

  async playErrorSound() {
    if (!this.isAudioEnabled) return;
    logDebug('Playing error sound');
    await this.playBeep(this.errorFrequency, 300);
    await delay(50); // Brief pause
    await this.playBeep(this.errorFrequency - 100, 200);
  }

  async playCompletionSound() {
    if (!this.isAudioEnabled) return; // Removed '|| !true' which was redundant
    logDebug('Playing completion sound');
    const melody = [
      { freq: 523, dur: 150 }, { freq: 659, dur: 150 },
      { freq: 784, dur: 150 }, { freq: 1047, dur: 300 }
    ];
    for (const note of melody) {
      await this.playBeep(note.freq, note.dur);
      await delay(50); // Delay between notes
    }
  }

  async playStartupSound() {
    if (!this.isAudioEnabled) return; // Removed '|| !true'
    logDebug('Playing startup sound');
    await this.playBeep(this.successFrequency - 200, 100);
    await delay(50);
    await this.playBeep(this.successFrequency, 100);
  }

  setAudioEnabled(enabled) {
    this.isAudioEnabled = !!enabled;
    // This logDebug might use the placeholder if called before initializeAudio completes its dynamic import.
    // This is generally acceptable for an early configuration log.
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

export const initializeAudio = () => audioManager.initialize();
export const playSuccessSound = (milestone) => audioManager.playSuccessSound(milestone);
export const playErrorSound = () => audioManager.playErrorSound();
export const playCompletionSound = () => audioManager.playCompletionSound();
export const playStartupSound = () => audioManager.playStartupSound();
export const setAudioEnabled = (enabled) => audioManager.setAudioEnabled(enabled);
export const getAudioStats = () => audioManager.getStats(); 