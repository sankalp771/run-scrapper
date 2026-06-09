# Vibe Race Tracker India

Live at : https://run-scrapper.vercel.app/

**Vibe Race Tracker India** is a full-stack developer-themed dashboard that aggregates, filters, and redirects users to upcoming major fitness and obstacle races across India (specifically HYROX India, Maruti Suzuki Arena Devils Circuit, and The Yodhaa Race).

## 🛠️ The Tech Stack
* **Frontend**: React / Next.js (TypeScript, custom Vanilla CSS Developer Dark Theme)
* **Backend**: Python (FastAPI, APScheduler, requests, BeautifulSoup4)
* **Data Storage**: Static JSON file-based database (`backend/events.json`)

---

## ⚡ Self-Healing Static Extraction Engine
Rather than running heavy, resource-intensive, and slow headless browsers (like Selenium or Playwright) which are prone to timing out and getting blocked by Cloudflare, the Python scraper:
1. Crawls the homepage of **Devils Circuit** and **Yodhaa** to find their dynamically generated Next.js production JS chunk paths.
2. Downloads the client-side JavaScript bundles directly.
3. Extracts the hardcoded static event lists and their registration/booking URLs (hosted on `getmybib.com`) using regular expressions.
4. Crawls **HYROX India**'s WordPress event listings and details pages to extract direct ticket shop URLs.
This approach executes in **milliseconds** rather than seconds and is highly reliable.

---

## 🚀 Running the Project

### 1. Start the Backend API
First, set up your Python virtual environment and run the backend FastAPI server:

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
On server startup, the scraper runs automatically to generate the `events.json` cache and initializes a background job to sync every **4 hours** using APScheduler.

API Endpoints:
* `GET http://127.0.0.1:8000/events`: Returns all upcoming races.
  * *Query parameters*: `city`, `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)
* `GET http://127.0.0.1:8000/status`: Returns status and last sync time for all scrapers.

---

### 2. Start the Frontend Dashboard
Navigate to the frontend directory and start the Next.js dev server:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open `http://localhost:3000` in your browser to view the dashboard.

---

## 📂 Directory Structure
* `backend/`
  * `main.py`: FastAPI server, lifespan setup, and background jobs
  * `scraper.py`: Raw crawler engines querying target sites directly
  * `normalizer.py`: Incremental diffing algorithms and schema parsing
  * `requirements.txt`: Python package requirements
  * `Dockerfile`: Container configurations for hosting
  * `.python-version`: Locks Render Python runtime to 3.11.9
* `frontend/`
  * `app/page.tsx`: NextJS dashboard and Datepicker
  * `app/layout.tsx`: HTML head layout configurations
  * `app/globals.css`: Custom Vanilla CSS themes and animations
  * `package.json`: Node dependencies and build scripts

---

## 🔧 Environment Variables

### Backend Configuration
* **`PYTHON_VERSION`** (Render environment): Set to `3.11.9` to avoid compilation errors on pre-release versions.

### Frontend Configuration
* **`NEXT_PUBLIC_API_URL`** (Vercel environment): Points to the deployed backend URL (e.g. `https://your-app.onrender.com`). Defaults to `http://127.0.0.1:8000` when running locally.

---

## 🌐 Production Deployment Architecture

* **Backend**: Deployed as a web service on **Render** (free tier).
  * **Keep-Alive Configuration**: A free cron job is set up on `cron-job.org` to ping `https://<your-backend>.onrender.com/status` every 12 minutes to prevent the free tier container from going to sleep.
* **Frontend**: Deployed on **Vercel** (free tier Next.js host), with the root directory set to `frontend/`.

---

## ⚡ Self-Healing Dynamic Database Caching
* The database is stored in a local JSON cache (`events.json`) inside the container.
* On startup (including container wake-ups), the server unconditionally runs the scraping cycle to fetch the latest details.
* The system performs an $O(N + M)$ linear-time diffing check:
  * **Additions**: New events are automatically populated.
  * **Updates**: Details that change are updated, resetting the `last_updated` timestamp.
  * **Preservation**: Unchanged events keep their original `last_updated` timestamp.
  * **Deletions**: Events removed from the source websites are dynamically deleted from the cache.

