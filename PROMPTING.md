# PROMPTING.md — AI Evolutionary Steps

This document outlines the milestones and prompts used during the development of the **Vibe Race Tracker India** full-stack application.

My WEB chats :
https://chatgpt.com/share/6a2796ed-feb0-8321-a524-b4eec9504dee
https://claude.ai/share/8735e5b7-b309-42fd-bd96-0fb92695d0c5

---

## 🎯 Milestone 1: Scraping Architecture & Platform Investigation

### 1. Initial Prompt
> Research how to programmatically extract upcoming races from `india.hyrox.co.in`, `devilscircuit.com`, and `theyoddharace.com`. Verify if we can scrape them using simple static requests or if we need a browser simulation framework like Playwright/Selenium.

### 2. AI Response
* The target websites return successful `200 OK` status codes for static requests.
* Devils Circuit and Yodhaa events lists are not immediately visible inside simple anchor links on the raw HTML because they are built using dynamic frontends (Next.js statically exported).
* Suggested writing a Playwright browser automation script to load pages and trigger button click events to extract registration URLs.

### 3. Error / Hallucination Encountered
* Running browser clicks using Playwright:
  - Takes a massive amount of time (15–20 seconds per card) to scroll, hover, click, catch popups, wait for redirection, and extract URLs.
  - Can get intercepted or trigger timeouts due to pointer intercepts on overlapping elements.
  - Is extremely heavy and fragile in a server context.

### 4. Follow-up Prompt
> Playwright clicking is too slow and unstable. Inspect the Next.js frontend script chunks loaded on these pages to see if the event data and ticketing URLs are statically compiled inside them.

### 5. Final Resolution
* Found that the entire event list with dates, titles, and `getmybib.com` booking URLs is statically hardcoded in Next.js client-side JS bundle chunks (e.g., `index-*.js` on Devils Circuit, and `526-*.js`/`2557-*.js` on Yodhaa).
* Created a lightweight Python scraper that dynamically reads chunk names from the page's HTML headers, downloads the static JS chunk file directly, and extracts the event array via regular expressions.
* **Benefit**: Scraping now takes less than 2 seconds, runs in standard python without headless browsers, has zero runtime dependencies on Chromium, and is completely immune to Cloudflare blocks.

---

## 🎯 Milestone 2: Frontend Dashboard & API Integration

### 1. Initial Prompt
> Initialize a Next.js TypeScript project in the `frontend` directory in non-interactive mode. Build a custom, high-fidelity developer dark theme layout using Vanilla CSS, showing event cards with brand-colored styling and a pulsing status dot.

### 2. AI Response
* Set up a Next.js App Router project and wrote `frontend/app/globals.css` with radial gradients, glassmorphism card properties, and a custom `@keyframes pulse` micro-animation.
* Wrote `frontend/app/page.tsx` with city filter pills, range picker dates, and layout cards.

### 3. Error / Hallucination Encountered
* During compilation (`npm run build`), the build failed with a TypeScript type error:
  `Type error: Cannot find name 'str'` in `Event` interface definition (typed `id: str;` instead of `id: string;` due to Python type habits).

### 4. Follow-up Prompt
> Fix the type compilation error in `page.tsx` by changing the `id` type from `str` to `string`.

### 5. Final Resolution
* Modified `page.tsx` to declare `id: string;`.
* Re-ran `npm run build` and the Next.js app compiled successfully.

---

## 🎯 Milestone 3: Scheduling & Reliability

### 1. Initial Prompt
> Integrate APScheduler into the FastAPI server so that the scraping engine runs automatically on server start and refreshes event caches every 4 hours.

### 2. AI Response
* Configured APScheduler's `BackgroundScheduler` inside FastAPI's async `lifespan` handler.
* Started the background jobs and verified that the scheduler successfully triggers and prints:
  `Started background scheduler for scraping every 4 hours.`
* The cached dataset remains persistently available at `backend/events.json`.

---

## 🎯 Milestone 4: Dual-Link (Info & Booking) UX Refinement

### 1. Initial Prompt
> I've a doubt, except Hyrox the other two directly send to payment instead of event pages... I think we need to send them to event page.

### 2. AI Response
* Verified that Devils Circuit and Yodhaa direct registration links go directly to raw, unbranded GetMyBib checkout forms.
* Investigated client bundles and tested path permutations to verify if they have dedicated, case-sensitive details pages:
  - Devils Circuit: `https://www.devilscircuit.com/city/{CityName}` (e.g. `/city/Jaipur`, `/city/Delhi%20NCR`)
  - The Yodhaa Race: `https://theyoddharace.com/city/{CityName}` (e.g. `/city/Mumbai`, `/city/Delhi`)
* Proposed and implemented a dual-button architecture (direct checkout + info details).

### 3. Error / Hallucination Encountered
* Feedback indicated that showing dual links (one direct to GetMyBib and one to info page) was cluttered and that cards should exclusively direct to the informative city event pages (matching the user experience of HYROX).

### 4. Follow-up Prompt
> no use of dual mode, only keep event page...

### 5. Final Resolution
* Reverted the card layout to a single, full-width "Book Now" CTA button.
* Configured the button redirect to target the official case-sensitive city event info pages directly (e.g. `https://www.devilscircuit.com/city/Chandigarh`).
* Cleaned up the frontend stylesheets, rebuilt the Next.js production build, and verified that clicking the single "Book Now" button correctly opens the informative event page.

---

## 🎯 Milestone 5: Production Deployment & Platform Optimization

### 1. Initial Prompt
> can you help me in deployment , how I gotta do this okay?

### 2. AI Response
* Identified that the Next.js frontend had hardcoded local API calls to `127.0.0.1:8000`. Refactored `frontend/app/page.tsx` to read the API base URL from `process.env.NEXT_PUBLIC_API_URL` with a local fallback.
* Proposed a dual-service deployment architecture: FastAPI backend on **Render** (free web service) and Next.js frontend on **Vercel** (free hosting).
* Created a helper `Dockerfile` in the backend directory to make containerized hosting easier.

### 3. Error / Hallucination Encountered
* During deployment, the Render build failed with a `metadata-generation-failed` error on the `pydantic-core` package.
* **Root Cause**: Render default environment was using Python 3.14 (an experimental pre-release version). Since pre-compiled wheels for Python 3.14 did not exist on PyPI, it tried compiling the Rust source code using `cargo` and `maturin`, which failed due to a read-only cache filesystem error:
  `Read-only file system (os error 30)`

### 4. Follow-up Prompt / Resolution
* Created `.python-version` files in the repository root and `backend/` directory specifying stable Python `3.11.9`.
* Pushed changes to GitHub, triggering a rebuild using Python 3.11 which successfully pulled pre-built wheels and deployed the API to production.
* Set up a free cron job on `cron-job.org` calling `https://run-scrapper.onrender.com/status` every 5 minutes to keep the Render free tier from going to sleep.
* Configured Vercel deployment pointing the root directory to `frontend` and supplying `NEXT_PUBLIC_API_URL` environment variable pointing to the Render backend URL.