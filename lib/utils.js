import crypto from 'crypto';
import { URL } from 'url';

/**
 * Utility functions for the YouTube Views Generator
 */

/**
 * Validate YouTube URL (supports regular videos and Shorts)
 */
function validateYouTubeUrl(url) {
  try {
    const parsedUrl = new URL(url);
    const hostname = parsedUrl.hostname.toLowerCase();
    const validDomains = [
      'youtube.com',
      'www.youtube.com',
      'm.youtube.com',
      'youtu.be'
    ];
    if (!validDomains.includes(hostname)) return false;
    let videoId = null;
    if (hostname === 'youtu.be') {
      videoId = parsedUrl.pathname.slice(1);
    } else {
      const pathname = parsedUrl.pathname;
      if (pathname.startsWith('/watch')) {
        videoId = parsedUrl.searchParams.get('v');
      } else if (pathname.startsWith('/shorts/')) {
        videoId = pathname.split('/shorts/')[1]?.split('?')[0];
      } else if (pathname.startsWith('/embed/')) {
        videoId = pathname.split('/embed/')[1]?.split('?')[0];
      }
    }
    return videoId && /^[a-zA-Z0-9_-]{11}$/.test(videoId);
  } catch (error) {
    return false;
  }
}

/**
 * Extract video ID from YouTube URL (supports regular videos and Shorts)
 */
function extractVideoId(url) {
  try {
    const parsedUrl = new URL(url);
    const hostname = parsedUrl.hostname.toLowerCase();
    if (hostname === 'youtu.be') {
      return parsedUrl.pathname.slice(1);
    } else {
      const pathname = parsedUrl.pathname;
      if (pathname.startsWith('/watch')) {
        return parsedUrl.searchParams.get('v');
      } else if (pathname.startsWith('/shorts/')) {
        return pathname.split('/shorts/')[1]?.split('?')[0];
      } else if (pathname.startsWith('/embed/')) {
        return pathname.split('/embed/')[1]?.split('?')[0];
      }
    }
  } catch (error) {
    return null;
  }
}

/**
 * Detect if URL is a YouTube Shorts video
 */
function isYouTubeShorts(url) {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.pathname.startsWith('/shorts/');
  } catch (error) {
    return false;
  }
}

/**
 * Get video type (regular or shorts)
 */
function getVideoType(url) {
  return isYouTubeShorts(url) ? 'shorts' : 'video';
}

/**
 * Generate random delay between min and max values (in milliseconds)
 */
function getRandomDelay(min = 1000, max = 5000) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Sleep/delay function
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Get random user agent from the configured pool or file
 */
function getRandomUserAgent() {
  const userAgents = config.userAgents;
  return userAgents[Math.floor(Math.random() * userAgents.length)];
}

/**
 * Get random viewport size from the configured pool
 */
function getRandomViewport() {
  const viewports = config.viewports;
  const viewport = viewports[Math.floor(Math.random() * viewports.length)];
  return {
    width: viewport.width + Math.floor(Math.random() * 20) - 10,
    height: viewport.height + Math.floor(Math.random() * 20) - 10
  };
}

/**
 * Generate random string
 */
function generateRandomString(length = 10) {
  return crypto.randomBytes(Math.ceil(length / 2)).toString('hex').slice(0, length);
}

/**
 * Generate random number between min and max (inclusive)
 */
function getRandomNumber(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Shuffle array using Fisher-Yates algorithm
 */
function shuffleArray(array) {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

/**
 * Format duration in seconds to human readable format
 */
function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
}

/**
 * Format number with thousand separators
 */
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Calculate success rate percentage
 */
function calculateSuccessRate(successful, total) {
  if (total === 0) return 0;
  return Math.round((successful / total) * 100);
}

/**
 * Check if string is empty or whitespace only
 */
function isEmpty(str) {
  return !str || str.trim().length === 0;
}

/**
 * Sanitize filename by removing invalid characters
 */
function sanitizeFilename(filename) {
  return filename.replace(/[<>:"/\\|?*]/g, '_').trim();
}

/**
 * Get timestamp string for logging (YYYY-MM-DD HH:MM:SS)
 */
function getTimestamp() {
  return new Date().toISOString();
}

/**
 * Create a retry wrapper for async functions
 */
function withRetry(fn, maxRetries = 3, delayMs = 1000) {
  return async function(...args) {
    let lastError;
    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await fn.apply(this, args);
      } catch (error) {
        lastError = error;
        if (i < maxRetries) {
          await delay(delayMs * (i + 1));
        }
      }
    }
    throw lastError;
  };
}

/**
 * Deep clone an object
 */
function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map(deepClone);
  }
  const cloned = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      cloned[key] = deepClone(obj[key]);
    }
  }
  return cloned;
}

/**
 * Check if running in debug mode based on LOG_LEVEL or DEBUG env var
 */
function isDebugMode() {
  return config.logging.enableDebug;
}

/**
 * Safe JSON parse with fallback
 */
function safeJsonParse(str, fallback = null) {
  try {
    return JSON.parse(str);
  } catch {
    return fallback;
  }
}

/**
 * Generate human-like mouse coordinates for puppeteer page.mouse.move
 */
function generateMousePath(startX, startY, endX, endY, steps = 10) {
  const path = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = Math.round(startX + (endX - startX) * t + Math.random() * 2 - 1);
    const y = Math.round(startY + (endY - startY) * t + Math.random() * 2 - 1);
    path.push({ x, y });
  }
  return path;
}

/**
 * Rate limiter utility
 */
class RateLimiter {
  constructor(maxCalls, windowMs) {
    this.maxCalls = maxCalls;
    this.windowMs = windowMs;
    this.calls = [];
  }
  canMakeCall() {
    const now = Date.now();
    this.calls = this.calls.filter(ts => now - ts < this.windowMs);
    return this.calls.length < this.maxCalls;
  }
  makeCall() {
    if (this.canMakeCall()) {
      this.calls.push(Date.now());
      return true;
    }
    return false;
  }
  getWaitTime() {
    if (this.canMakeCall()) return 0;
    const now = Date.now();
    const earliest = Math.min(...this.calls);
    return this.windowMs - (now - earliest);
  }
}

export {
  validateYouTubeUrl,
  extractVideoId,
  isYouTubeShorts,
  getVideoType,
  getRandomDelay,
  delay,
  getRandomUserAgent,
  getRandomViewport,
  generateRandomString,
  getRandomNumber,
  shuffleArray,
  formatDuration,
  formatNumber,
  calculateSuccessRate,
  isEmpty,
  sanitizeFilename,
  getTimestamp,
  withRetry,
  deepClone,
  isDebugMode,
  safeJsonParse,
  generateMousePath,
  RateLimiter
}; 