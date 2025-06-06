// TorManager: Handles Tor initialization, IP rotation, and proxy agent management for the CLI app.
import { SocksProxyAgent } from 'socks-proxy-agent';
import net from 'net';
import * as ui from './ui.js';
import { delay } from './utils.js';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

// Helper to load config/paths.json
function getTorBinaryPath() {
  try {
    const configPath = path.resolve('config/paths.json');
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
      return config.torPath || null;
    }
  } catch (e) {}
  return null;
}

// Helper to check if Tor is running on the given port
function isTorRunning(host, port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(2000);
    socket.connect(port, host, () => {
      socket.destroy();
      resolve(true);
    });
    socket.on('error', () => resolve(false));
    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });
  });
}

// Helper to start Tor process
async function ensureTorRunning(host, port) {
  const running = await isTorRunning(host, port);
  if (running) return;
  const torPath = getTorBinaryPath();
  if (!torPath || !fs.existsSync(torPath)) {
    ui.logError('Tor binary not found. Please run `npm run setup` and ensure Tor is installed.');
    throw new Error('Tor binary not found');
  }
  ui.logInfo(`Starting Tor from: ${torPath}`);
  const torProc = spawn(torPath, [], { detached: true, stdio: 'ignore' });
  torProc.unref();
  // Wait for Tor to be available
  for (let i = 0; i < 10; i++) {
    if (await isTorRunning(host, port)) {
      ui.logSuccess('Tor started successfully.');
      return;
    }
    await delay(1000);
  }
  ui.logError('Failed to start Tor automatically. Please check your Tor installation.');
  throw new Error('Failed to start Tor');
}

class TorManager {
  constructor() {
    this.proxyAgent = null;
    this.isInitialized = false;
    this.rotationCount = 0;
    this.lastRotation = 0;
    this.torConfig = null;
  }

  // Initialize Tor with the given config (host, port, etc.)
  async initTor(torConfig) {
    try {
      // Ensure Tor is running before proceeding
      await ensureTorRunning(torConfig.host, torConfig.port);
      this.torConfig = torConfig;
      this.proxyAgent = new SocksProxyAgent(torConfig.socksUrl || `socks5://${torConfig.host}:${torConfig.port}`);
      await this.checkTorStatus();
      this.isInitialized = true;
      ui.logInfo('Tor initialized successfully');
      return true;
    } catch (error) {
      ui.logError(`Failed to initialize Tor: ${error.message}`);
      throw error;
    }
  }

  // Check if Tor is reachable on the configured port
  async checkTorStatus() {
    const cfg = this.torConfig;
    return new Promise((resolve, reject) => {
      const socket = new net.Socket();
      socket.setTimeout(cfg.connectionTimeout || 10000);
      socket.connect(cfg.port, cfg.host, () => {
        socket.destroy();
        resolve(true);
      });
      socket.on('error', (error) => {
        reject(new Error(`Tor connection failed: ${error.message}`));
      });
      socket.on('timeout', () => {
        socket.destroy();
        reject(new Error('Tor connection timeout'));
      });
    });
  }

  // Get the current public IP as seen through Tor
  async getCurrentIP() {
    try {
      const fetch = (await import('node-fetch')).default;
      const response = await fetch('https://httpbin.org/ip', {
        agent: this.proxyAgent,
        timeout: 10000
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      return data.origin;
    } catch (error) {
      throw new Error(`Failed to get current IP: ${error.message}`);
    }
  }

  // Rotate the Tor IP by sending a NEWNYM command to the control port
  async rotateIP() {
    const cfg = this.torConfig;
    try {
      const now = Date.now();
      const minRotationInterval = cfg.minRotationInterval || 10000;
      const timeSinceLastRotation = now - this.lastRotation;
      if (timeSinceLastRotation < minRotationInterval) {
        const waitTime = minRotationInterval - timeSinceLastRotation;
        await delay(waitTime);
      }
      await this.sendControlCommand('NEWNYM');
      await delay(cfg.circuitBuildTime || 15000); // Wait for new circuit
      this.rotationCount++;
      this.lastRotation = Date.now();
      ui.logInfo(`IP rotated (${this.rotationCount} total rotations)`);
      return true;
    } catch (error) {
      ui.logError(`IP rotation failed: ${error.message}`);
      return false;
    }
  }

  // Send a command to the Tor control port (e.g., NEWNYM for new identity)
  async sendControlCommand(command) {
    const cfg = this.torConfig;
    return new Promise((resolve, reject) => {
      const socket = new net.Socket();
      socket.setTimeout(5000);
      socket.connect(cfg.controlPort, cfg.host, () => {
        if (cfg.controlPassword) {
          socket.write(`AUTHENTICATE \"${cfg.controlPassword}\"\r\n`);
        } else {
          socket.write('AUTHENTICATE\r\n');
        }
        socket.write(`${command}\r\n`);
        socket.write('QUIT\r\n');
      });
      let response = '';
      socket.on('data', (data) => {
        response += data.toString();
      });
      socket.on('close', () => {
        if (response.includes('250 OK')) {
          resolve(response);
        } else {
          reject(new Error(`Control command failed: ${response}`));
        }
      });
      socket.on('error', (error) => {
        reject(new Error(`Control connection error: ${error.message}`));
      });
      socket.on('timeout', () => {
        socket.destroy();
        reject(new Error('Control command timeout'));
      });
    });
  }

  // Get the proxy agent for use in HTTP requests
  getProxyAgent() {
    if (!this.isInitialized) {
      throw new Error('Tor not initialized');
    }
    return this.proxyAgent;
  }

  // Get the proxy config for Puppeteer or other modules
  getProxyConfig() {
    const cfg = this.torConfig;
    return {
      server: cfg.socksUrl || `socks5://${cfg.host}:${cfg.port}`,
      username: cfg.username,
      password: cfg.password
    };
  }

  // Get Tor statistics for UI display
  getStats() {
    return {
      isInitialized: this.isInitialized,
      rotationCount: this.rotationCount,
      lastRotation: this.lastRotation,
      timeSinceLastRotation: Date.now() - this.lastRotation
    };
  }

  // Cleanup Tor state (for future extensibility)
  async cleanup() {
    this.isInitialized = false;
    ui.logInfo('Tor cleanup completed');
  }
}

const torManager = new TorManager();

// ESM-compliant named exports for all TorManager methods
export const initTor = (torConfig) => torManager.initTor(torConfig);
export const checkTorStatus = () => torManager.checkTorStatus();
export const getCurrentIp = () => torManager.getCurrentIP();
export const rotateIP = () => torManager.rotateIP();
export const getProxyAgent = () => torManager.getProxyAgent();
export const getProxyConfig = () => torManager.getProxyConfig();
export const getTorStats = () => torManager.getStats();
export const cleanup = () => torManager.cleanup(); 