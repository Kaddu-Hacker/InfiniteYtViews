// ProxyPool: Manages fetching, validating, and rotating HTTP/SOCKS proxies for the CLI app.
const https = require('https');
const http = require('http');
const net = require('net');
const ui = require('./ui');
const { delay } = require('./utils');

class ProxyPool {
  constructor() {
    this.proxies = [];
    this.currentIndex = 0;
    this.validatedProxiesInfo = new Map();
    this.lastFetchTime = 0;
    this.isFetching = false;
    this.isValidating = false;
    this.proxyConfig = {
      sources: [],
      refreshInterval: 3600000, // 1 hour
      validationTimeout: 10000, // 10 seconds
      revalidateInterval: 300000 // 5 minutes
    };
  }

  // Initialize proxy pool with config (sources, intervals, etc.)
  init(config) {
    this.proxyConfig = {
      ...this.proxyConfig,
      ...(config || {})
    };
  }

  // Fetch proxies from all configured sources
  async fetchProxies(force = false) {
    if (this.isFetching) {
      ui.logDebug('Proxy fetch already in progress.');
      return this.proxies;
    }
    const now = Date.now();
    if (!force && (now - this.lastFetchTime < this.proxyConfig.refreshInterval)) {
      ui.logDebug('Proxy list is recent, skipping fetch. Use force=true to override.');
      return this.proxies;
    }

    this.isFetching = true;
    const proxySources = this.proxyConfig.sources;
    if (!proxySources || proxySources.length === 0) {
      ui.logWarning('No proxy sources configured. Cannot fetch proxies.');
      this.isFetching = false;
      return [];
    }

    ui.logInfo(`Fetching fresh proxy lists from ${proxySources.length} source(s)...`);
    const spinner = ui.createSpinner('Fetching proxy sources...');
    spinner.start();

    const allFetchedProxies = new Set();

    for (const sourceUrl of proxySources) {
      try {
        spinner.updateText(`Fetching from ${sourceUrl}...`);
        const proxyListData = await this.fetchFromSource(sourceUrl);
        const parsedProxies = this.parseProxyList(proxyListData, sourceUrl);
        parsedProxies.forEach(p => allFetchedProxies.add(p.url));
        ui.logDebug(`Fetched ${parsedProxies.length} potential proxies from ${sourceUrl}.`);
      } catch (error) {
        ui.logError(`Failed to fetch or parse proxies from ${sourceUrl}: ${error.message}`);
      }
    }

    // Deduplicate and format proxies
    this.proxies = Array.from(allFetchedProxies).map(proxyUrl => {
        try {
            const urlParts = new URL(proxyUrl);
            return {
                host: urlParts.hostname,
                port: parseInt(urlParts.port),
                type: urlParts.protocol.replace(':', ''),
                url: proxyUrl,
                sourceUrl: 'various',
                validated: false,
                lastChecked: 0,
            };
        } catch (e) {
            ui.logWarning(`Invalid proxy URL format in deduped list: ${proxyUrl}`);
            return null;
        }
    }).filter(p => p !== null);

    this.lastFetchTime = Date.now();
    this.isFetching = false;
    spinner.succeed(`Fetched ${this.proxies.length} unique proxy entries from ${proxySources.length} source(s).`);
    
    if (this.proxies.length > 0) {
        this.validateAllProxies(true);
    }
    return this.proxies;
  }

  // Fetch proxy list from a single source URL
  async fetchFromSource(url) {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https') ? https : http;
      const request = client.get(url, {
        timeout: this.proxyConfig.validationTimeout,
        headers: { 'User-Agent': 'Mozilla/5.0 (Node.js Proxy Pool Fetcher)' }
      }, (response) => {
        let data = '';
        if (response.statusCode !== 200) {
          response.resume();
          return reject(new Error(`Failed to get proxy list from ${url}. Status: ${response.statusCode}`));
        }
        response.on('data', chunk => data += chunk);
        response.on('end', () => resolve(data));
      });
      request.on('error', err => reject(new Error(`Error fetching proxy list from ${url}: ${err.message}`)));
      request.on('timeout', () => {
        request.destroy();
        reject(new Error(`Timeout fetching proxy list from ${url}`));
      });
    });
  }

  // Parse proxy list text into proxy objects
  parseProxyList(textData, sourceUrl) {
    const proxies = [];
    const lines = textData.split(/\r?\n/);
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//')) continue;

      let match = trimmed.match(/^(\w+):\/\/((?:[0-9]{1,3}\.){3}[0-9]{1,3}):([0-9]{1,5})$/i);
      let type = 'http';
      let host, port, proxyUrlString;

      if (match) {
        type = match[1].toLowerCase();
        host = match[2];
        port = parseInt(match[3]);
        proxyUrlString = `${type}://${host}:${port}`;
      } else {
        match = trimmed.match(/^((?:[0-9]{1,3}\.){3}[0-9]{1,3}):([0-9]{1,5})$/);
        if (match) {
          host = match[1];
          port = parseInt(match[2]);
          if (sourceUrl.toLowerCase().includes('socks')) type = 'socks5';
          proxyUrlString = `${type}://${host}:${port}`; 
        } else {
            continue;
        }
      }
        proxies.push({ host, port, type, url: proxyUrlString, sourceUrl });
    }
    return proxies;
  }

  // Validate a single proxy by attempting a TCP connection
  async validateProxy(proxy, timeout = this.proxyConfig.validationTimeout) {
    return new Promise((resolve) => {
      const socket = new net.Socket();
      socket.setTimeout(timeout);
      const startTime = Date.now();

      socket.connect(proxy.port, proxy.host, () => {
        const responseTime = Date.now() - startTime;
        socket.destroy();
        resolve({ valid: true, responseTime, lastChecked: Date.now() });
      });
      socket.on('error', (err) => {
        socket.destroy();
        resolve({ valid: false, error: err.message, lastChecked: Date.now() });
      });
      socket.on('timeout', () => {
        socket.destroy();
        resolve({ valid: false, error: 'Timeout', lastChecked: Date.now() });
      });
    });
  }

  // Validate all proxies in the pool (batch, with progress)
  async validateAllProxies(isNewFetch = false) {
    if (this.isValidating) {
      ui.logDebug('Proxy validation already in progress.');
      return;
    }
    if (this.proxies.length === 0) {
      ui.logInfo('Proxy list is empty. Nothing to validate.');
      return;
    }

    this.isValidating = true;
    const spinner = ui.createSpinner(`Validating ${this.proxies.length} proxies...`);
    spinner.start();

    const proxiesToValidate = isNewFetch ? 
        this.proxies : 
        this.proxies.filter(p => {
            const validationInfo = this.validatedProxiesInfo.get(p.url);
            return !validationInfo || (Date.now() - validationInfo.lastChecked > this.proxyConfig.revalidateInterval);
        });

    if (proxiesToValidate.length === 0) {
        spinner.succeed('No proxies requiring validation at this time.');
        this.isValidating = false;
        return;
    }
    
    spinner.updateText(`Validating ${proxiesToValidate.length} proxies...`);
    let validatedCount = 0;
    const batchSize = 20;

    for (let i = 0; i < proxiesToValidate.length; i += batchSize) {
      const batch = proxiesToValidate.slice(i, i + batchSize);
      spinner.updateText(`Validating batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(proxiesToValidate.length/batchSize)} (${batch.length} proxies)...`);
      const batchPromises = batch.map(async (proxy) => {
        const result = await this.validateProxy(proxy);
        this.validatedProxiesInfo.set(proxy.url, result);
        if (result.valid) {
            const mainProxy = this.proxies.find(p => p.url === proxy.url);
            if(mainProxy) {
                mainProxy.validated = true;
                mainProxy.lastChecked = result.lastChecked;
            }
            validatedCount++;
        }
        return { proxyUrl: proxy.url, ...result };
      });
      await Promise.all(batchPromises);
      if (i + batchSize < proxiesToValidate.length) {
        await delay(1000);
      }
    }

    const totalCurrentlyValid = Array.from(this.validatedProxiesInfo.values()).filter(v => v.valid).length;
    spinner.succeed(`Validation complete. ${validatedCount} newly checked proxies were valid. Total currently valid in pool: ${totalCurrentlyValid}.`);
    this.isValidating = false;
  }

  // Get the next working proxy (rotates through validated proxies)
  async getNextProxy() {
    if (this.proxies.length === 0 && !this.isFetching) {
      ui.logInfo('Proxy pool is empty, attempting to fetch...');
      await this.fetchProxies(true);
    }
    if (this.proxies.length === 0) {
      ui.logError('Proxy pool is empty and fetch failed. No proxies available.');
      return null;
    }

    const workingProxies = this.proxies.filter(p => {
        const validationInfo = this.validatedProxiesInfo.get(p.url);
        return validationInfo && validationInfo.valid;
    });

    if (workingProxies.length === 0) {
      ui.logWarning('No validated proxies currently available in the pool. Attempting re-validation...');
      await this.validateAllProxies();
      const newWorkingProxies = this.proxies.filter(p => {
        const validationInfo = this.validatedProxiesInfo.get(p.url);
        return validationInfo && validationInfo.valid;
      });
      if (newWorkingProxies.length === 0) {
        ui.logError('Still no working proxies after re-validation attempt.');
        return null;
      }
      this.currentIndex = 0;
      return newWorkingProxies[this.currentIndex].url;
    }

    this.currentIndex = (this.currentIndex + 1) % workingProxies.length;
    const selectedProxy = workingProxies[this.currentIndex];
    ui.logInfo(`Using proxy: ${selectedProxy.url} (from ${selectedProxy.sourceUrl || 'various'})`);
    return selectedProxy.url;
  }

  // Get proxy pool statistics for UI display
  getStats() {
    const totalProxies = this.proxies.length;
    const validatedEntries = Array.from(this.validatedProxiesInfo.values());
    const workingCount = validatedEntries.filter(p => p.valid).length;
    const lastCheckedTimes = validatedEntries.map(p => p.lastChecked).filter(Boolean);
    const lastValidatedTime = lastCheckedTimes.length > 0 ? Math.max(...lastCheckedTimes) : 0;

    return {
      totalProxies,
      workingProxies: workingCount,
      lastFetchTime: this.lastFetchTime,
      lastValidatedTime,
      isFetching: this.isFetching,
      isValidating: this.isValidating,
    };
  }
}

const proxyPool = new ProxyPool();

// Exported API for the rest of the app
module.exports = {
  initProxyPool: (configOrOptions = {}) => {
    proxyPool.init(configOrOptions);
    return proxyPool.fetchProxies(true);
  },
  fetchProxies: (force = false) => proxyPool.fetchProxies(force),
  validateAllProxies: (isNewFetch = false) => proxyPool.validateAllProxies(isNewFetch),
  getNextProxy: () => proxyPool.getNextProxy(),
  getProxyStats: () => proxyPool.getStats(),
};