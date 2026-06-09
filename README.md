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
  * `main.py`: FastAPI server & scheduler setup
  * `scraper.py`: Raw scraper functions for all three websites
  * `normalizer.py`: Standardizes dates, formats cities, validates schema
  * `requirements.txt`: Python package requirements
  * `events.json`: Aggregated local database of events
  * `status.json`: Last refresh and health logs
* `frontend/`
  * `app/page.tsx`: Main React dashboard with filtering and feed logic
  * `app/layout.tsx`: HTML layout and metadata configurations
  * `app/globals.css`: Custom Vanilla CSS stylesheets and animations
  * `package.json`: Node dependencies
