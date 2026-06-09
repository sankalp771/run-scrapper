# Backend Architectural Design Decisions & Reasoning

This document explains the technical choices, optimizations, and reasons behind the implementation details of the Vibe Race Tracker India Python backend.

---

## 1. Next.js Client Bundle Scraping vs. Browser Automation (Selenium/Playwright)

### The Challenge
Both **Devils Circuit** and **The Yodhaa Race** use dynamic React frontends (Next.js statically exported). Their event details and direct booking links are not present in the raw, static HTML returned by a basic HTTP GET request.
Normally, developers solve this by spinning up a headless browser (Playwright or Selenium) to load the page, wait for scripts to execute, click cards, and scrape the redirected pages.

### Our Solution
We analyze the page's HTML headers, dynamically fetch the Next.js production javascript bundle chunks (e.g. `/_next/static/chunks/pages/index-[hash].js`), and run Python Regular Expressions (`re.findall`) to parse the hardcoded static event arrays inside the JS code.

### The Reasoning
- **Resource Consumption**: Headless browsers require Chromium/Firefox binaries, consuming huge amounts of memory and CPU. Our regex bundle parser runs on standard light Python requests.
- **Speed**: Loading a headless browser, waiting for pages, clicking elements, and catching redirects takes **15 to 20 seconds**. Our Next.js chunk extraction takes **under 200 milliseconds**.
- **Reliability & Bot-Bypassing**: Headless browsers are easily caught by Cloudflare, triggering CAPTCHAs and blocks. Downloading static JS script assets behaves exactly like a standard browser asset download and is completely immune to Cloudflare/security blocks.

---

## 2. Unconditional Scraper Execution on Startup (Lifespan Lifecycle)

### The Challenge
On Render's free tier, the web container spins down and falls asleep after 15 minutes of inactivity. When a new user request or the cron job wakes it up, it starts a fresh boot cycle.
If the scraper only runs when the cache `events.json` is missing or empty, it will check the file structure. Since git tracks the codebase, there might be a static `events.json` checked in from local runs, which prevents the scraper from updating, resulting in stale data.

### Our Solution
We removed the conditional file check from the FastAPI `lifespan` startup logic. The scraping and diffing cycle now runs **unconditionally** every time the server boots up.

### The Reasoning
- Every container wake-up or deployment guarantees that the cache is self-healed and populated with the absolute latest, live-crawled events from the source websites.
- By wrapping the startup scraper call in a defensive `try...except` block, we ensure that if any external site is down or network timeouts occur, the API still boots successfully and serves the last available disk cache instead of crashing.

---

## 3. $O(N + M)$ Linear-Time Event Diffing

### The Challenge
If the scraper simply overwrote the cache on every cycle:
1. Every event's `last_updated` field would reset to the current time, losing the history of when it was actually modified.
2. If an event was cancelled or removed from the source site, it would remain in our cache indefinitely unless we wiped the cache manually.
3. A naive comparison loop ($O(N \times M)$) would degrade in performance as the list of events grows.

### Our Solution
We implemented a dictionary-based diffing algorithm (`diff_and_normalize`) in `normalizer.py`:
- Existing database cache items are mapped into a hash map indexed by their unique ID (`organizer_city_startdate`).
- We loop through new scraped events once, querying the hash map in $O(1)$ constant time.
- If the event exists, we compare all display details. If anything has changed, we overwrite it and update the `last_updated` timestamp. If they are identical, we preserve the original record and its original timestamp.
- Any event not present in the newly scraped events is discarded, fulfilling the dynamic deletion requirement.

### The Reasoning
- **Performance**: The lookup is linear-time ($O(N + M)$) where $N$ is the number of cached items and $M$ is the number of scraped items.
- **Data Integrity**: Preserves original timestamps, allowing the frontend to show which cards were recently edited.
- **Self-Cleaning**: Deletions on source websites propagate to our dashboard within the next scrape cycle.

---

## 4. Python Version Pinning (3.11.9)

### The Challenge
Render default builds run on the latest experimental Python 3.14. Because Python 3.14 lacks pre-compiled package binaries ("wheels") on PyPI for Pydantic/Rust libraries, pip attempts to compile the source code using Cargo, which fails on Render's read-only cache directories.

### Our Solution
We placed `.python-version` files in the repository root and `backend/` directory, locking the runtime to `3.11.9`.

### The Reasoning
- Python 3.11 is extremely stable and has pre-built wheels for all dependencies on PyPI.
- By pinning the version, the packages are pulled pre-compiled, completing the Render deployment build in seconds and avoiding compile-time errors.
