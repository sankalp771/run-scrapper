# PROMPTING.md — AI Evolutionary Steps

This document outlines the milestones and prompts used during the development of the **Vibe Race Tracker India** full-stack application.

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
* Proposed and implemented a dual-button architecture on event cards:
  - **Book Now** (primary, styled gradient CTA button linking to GetMyBib direct ticketing form).
  - **Event Details** (secondary, branded outline button linking to the official city details page).

### 3. Error / Hallucination Encountered
* Calling `/events` immediately after edits returned `ticket_url: null` because the persistent JSON cache `events.json` was generated before the new normalizer and schema changes were loaded by the server process.

### 4. Follow-up Prompt
* Restart the backend server so the API re-evaluates the updated Pydantic schema structure and trigger the POST `/refresh` endpoint to regenerate the cached records.

### 5. Final Resolution
* Restarted Uvicorn and posted to `/refresh` to flush the old data structures.
* Verified that the updated cards now show both buttons side-by-side: direct-to-checkout and official info page paths.

