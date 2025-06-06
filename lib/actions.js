import { logInfo, logError, logSuccess, startSpinner, stopSpinner, failSpinner } from './ui.js';
import { validateYouTubeUrl, delay } from './utils.js'; // Added delay to imports

/**
 * Simulates random scrolling on the page to mimic human behavior.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 */
async function randomHumanLikeScroll(page) {
  try {
    const scrollAmount = Math.floor(Math.random() * 300) + 100; // Scroll between 100 and 400 pixels
    const scrollDirection = Math.random() < 0.5 ? -1 : 1; // Scroll up or down
    await page.evaluate((amount, direction) => {
      window.scrollBy(0, amount * direction);
    }, scrollAmount, scrollDirection);
    logInfo(`Scrolled page by ${scrollAmount * scrollDirection}px`);
    await delay(Math.random() * 1000 + 500); // Wait 0.5-1.5s after scroll
  } catch (error) {
    logError(`Error during scrolling: ${error.message}`);
  }
}

/**
 * Simulates some basic, somewhat randomized mouse movements on the page.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 */
async function moveMouseHumanLike(page) {
  try {
    const viewport = page.viewport();
    const targetX = Math.floor(Math.random() * viewport.width);
    const targetY = Math.floor(Math.random() * viewport.height);
    const steps = Math.floor(Math.random() * 5) + 5; // 5-9 steps for movement

    logInfo(`Moving mouse to X:${targetX}, Y:${targetY} in ${steps} steps.`);
    await page.mouse.move(targetX, targetY, { steps });
    await delay(Math.random() * 500 + 200); // Wait 0.2-0.7s after mouse move
  } catch (error) {
    logError(`Error during mouse movement: ${error.message}`);
  }
}

/**
 * Attempts to find and click a play button, or interacts with the video player area.
 * This is a very basic attempt and might need significant improvement for reliability.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 */
async function attemptToPlayVideo(page) {
  logInfo('Attempting to play video...');
  try {
    // Common selectors for YouTube play buttons
    const playButtonSelectors = [
      'button[aria-label="Play (k)"]',
      'button[aria-label="Play"]' /* General play button */,
      '.ytp-large-play-button', // Large play button in the center
      '.html5-main-video', // Clicking the video element itself often plays/pauses
      '#movie_player', // The player container
    ];

    let clickedPlay = false;
    for (const selector of playButtonSelectors) {
      const button = await page.$(selector);
      if (button) {
        logInfo(`Found potential play button/element with selector: ${selector}`);
        await button.click({ delay: Math.random() * 100 + 50 }); // Add small random delay to click
        logSuccess('Clicked play button/element.');
        clickedPlay = true;
        await delay(2000); // Wait for video to hopefully start
        break;
      }
    }

    if (!clickedPlay) {
      logWarning('Could not find a specific play button. Video might autoplay or need different interaction.');
      // As a fallback, try focusing the player and sending a space key press
      const player = await page.$('#movie_player, .html5-video-player');
      if (player) {
        await player.focus();
        await page.keyboard.press('Space');
        logInfo('Focused player and pressed Space key as a fallback to play.');
        await delay(2000);
      }
    }
    return true;
  } catch (error) {
    logError(`Error attempting to play video: ${error.message}`);
    return false;
  }
}

/**
 * Watches a YouTube video for a specified duration, performing human-like actions.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 * @param {string} videoUrl - The URL of the YouTube video.
 * @param {number} watchDurationSeconds - The desired duration to watch the video in seconds.
 * @param {object} config - The application's final configuration object (not used yet, but for future).
 * @returns {Promise<boolean>} True if watching process completed (even if with minor errors), false on critical failure.
 */
async function watchVideo(page, videoUrl, watchDurationSeconds, config) {
  startSpinner(`Navigating to video: ${videoUrl}`);
  try {
    await page.goto(videoUrl, { waitUntil: 'networkidle2', timeout: 60000 });
    stopSpinner(true, `Navigated to video: ${videoUrl}`);
  } catch (error) {
    const errMsg = `Failed to navigate to video ${videoUrl}: ${error.message}`;
    failSpinner(errMsg);
    logError(errMsg);
    return false;
  }

  await delay(Math.random() * 2000 + 1000); // Wait 1-3 seconds for page to settle

  if (!await attemptToPlayVideo(page)) {
    logWarning('Video playback might not have started. Continuing watch attempt anyway.');
    // Depending on strictness, could return false here
  }

  const startTime = Date.now();
  const watchDurationMs = watchDurationSeconds * 1000;
  logInfo(`Starting to watch video for ${watchDurationSeconds} seconds...`);
  startSpinner('Watching video...');

  let lastActionTime = Date.now();

  while (Date.now() - startTime < watchDurationMs) {
    const remainingTimeMs = watchDurationMs - (Date.now() - startTime);
    if (remainingTimeMs <= 0) break;

    // Perform an action (scroll or mouse move) periodically
    if (Date.now() - lastActionTime > (Math.random() * 15000 + 10000)) { // 10-25 seconds between actions
      if (Math.random() < 0.6) { // 60% chance to scroll
        await randomHumanLikeScroll(page);
      } else { // 40% chance to move mouse
        await moveMouseHumanLike(page);
      }
      lastActionTime = Date.now();
    }
    
    // Check video state (playing, paused, ended) - VERY BASIC, needs improvement
    try {
        const isPaused = await page.$eval('.html5-video-player', el => el.classList.contains('paused-mode'));
        if (isPaused) {
            logWarning('Video seems to be paused. Attempting to resume...');
            await attemptToPlayVideo(page); // Try to play again if paused
        }
    } catch(e) {
        // Ignore if player state cannot be determined, might not be fully loaded or selector changed
    }


    await delay(2000); // Wait 2 seconds before next check loop
  }

  const successMsg = `Finished watching video for approximately ${watchDurationSeconds} seconds.`;
  stopSpinner(true, successMsg);
  logSuccess(successMsg);
  return true;
}

/**
 * Introduces a random delay between two values.
 * @param {number} minSeconds - Minimum seconds to sleep.
 * @param {number} maxSeconds - Maximum seconds to sleep.
 * @returns {Promise<void>}
 */
async function randomSleep(minSeconds, maxSeconds) {
  if (minSeconds <= 0 || maxSeconds <= 0 || minSeconds > maxSeconds) {
    logWarning('Invalid min/max seconds for randomSleep. Using default 5-15s.');
    minSeconds = 5;
    maxSeconds = 15;
  }
  const sleepTimeMs = Math.floor(Math.random() * (maxSeconds - minSeconds + 1) + minSeconds) * 1000;
  logInfo(`Sleeping for ${sleepTimeMs / 1000} seconds before next view cycle...`);
  startSpinner('Taking a short break...');
  await delay(sleepTimeMs);
  stopSpinner(true, 'Break finished.');
}

/**
 * Attempts to find and click the "like" button on a YouTube video page.
 * @param {import('puppeteer').Page} page - The Puppeteer page object.
 * @returns {Promise<boolean>} True if the like button was clicked, false otherwise.
 */
async function likeVideo(page) {
  logInfo('Attempting to like the video...');
  try {
    // YouTube selectors can be volatile. This selector targets buttons with an aria-label
    // that typically corresponds to the "like" button. It tries common variations.
    // It might need to be updated if YouTube changes its UI structure.
    const likeButtonSelector = 'button[aria-label*="like this video"], button[aria-label*="Like this video"], button[aria-label*="I like this"]'; // Added "I like this" as another common variant.

    await page.waitForSelector(likeButtonSelector, { timeout: 10000, visible: true });
    const likeButton = await page.$(likeButtonSelector);

    if (likeButton) {
      // Get the current pressed state. If it's already pressed, we might not want to click it again (to unlike).
      // This is a common pattern for toggle buttons.
      const isPressed = await page.evaluate(el => el.getAttribute('aria-pressed') === 'true', likeButton);

      if (isPressed) {
        logInfo('Video already liked.');
        return true; // Indicate success, as the goal (video is liked) is met.
      }

      await delay(Math.random() * 500 + 200); // Short random delay before click
      await likeButton.click({ delay: Math.random() * 50 + 50 }); // Simulate human-like click speed
      await delay(Math.random() * 500 + 500); // Short random delay after click

      // Check if the button state changed to "pressed"
      const واPressedAfterClick = await page.evaluate(el => el.getAttribute('aria-pressed') === 'true', likeButton);
      if (واPressedAfterClick) {
        logSuccess('Successfully liked the video!');
        return true;
      } else {
        // This might happen if the click didn't register the "like" (e.g., it unliked a previously liked video by another means)
        // or if the aria-pressed attribute isn't immediately updated or used consistently.
        logWarning('Clicked the like button, but confirmation of "liked" state failed. The video might have been unliked or the state attribute is inconsistent.');
        return false; // Or true depending on desired strictness. For now, false if not confirmed liked.
      }
    } else {
      logWarning('Like button not found with the current selectors.');
      return false;
    }
  } catch (error) {
    if (error.name === 'TimeoutError') {
      logWarning(`Like button not found within timeout: ${likeButtonSelector}`);
    } else {
      logError(`Error liking video: ${error.message}`);
    }
    return false;
  }
}

// ESM-compliant named exports for all actions methods
export { randomHumanLikeScroll, moveMouseHumanLike, watchVideo, attemptToPlayVideo, randomSleep, likeVideo }; 