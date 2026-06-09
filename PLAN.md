# PLAN.md

# Vibe Race Tracker India

## Objective

Build a full-stack application that aggregates upcoming fitness racing and obstacle course racing (OCR) events across India from multiple organizers into a single discovery dashboard.

The platform will:

* Programmatically scrape live event data
* Normalize heterogeneous event formats into a common schema
* Provide filtering and discovery capabilities
* Redirect users to official booking portals
* Refresh event information automatically

Target Organizers:

1. HYROX India
2. Maruti Suzuki Arena Devils Circuit
3. The Yodhaa Race

---
# 🛠️ The Tech Stack
Frontend: React / Next.js
Backend: Python 

# System Architecture

External Event Sources
↓
Scrapers
↓
Normalization Layer
↓
Unified Event Dataset
↓
FastAPI Backend
↓
Next.js Dashboard
↓
User Filters & Booking Redirects

---

# Normalized Event Schema

Every organizer returns data in different formats.
The backend converts all data into a single schema.

```json
{
  "id": "hyrox_mumbai_2026",
  "organizer": "HYROX",
  "event_name": "Masters' Union HYROX Mumbai",
  "city": "Mumbai",
  "venue": "NESCO Hall 6",
  "start_date": "2026-09-17",
  "end_date": "2026-09-20",
  "booking_url": "https://...",
  "source_url": "https://...",
  "last_updated": "2026-06-09T12:00:00"
}
```

---

# Phase 1 — Scraping & Data Extraction

## Goal

Extract upcoming race events directly from official organizer platforms.

## Deliverables

### HYROX Scraper

Extract:
* Event Name
* City
* Venue
* Event Dates
* Registration Link

### Devils Circuit Scraper

Extract:
* City
* Race Date
* Registration Link

### Yodhaa Race Scraper

Extract:
* City
* Race Date
* Registration Link

### Aggregator

Combine all organizer events into one dataset.

### Output

events.json

---

## Test Cases

### HYROX

PASS if:
* Upcoming events detected
* Mumbai event extracted correctly
* Delhi event extracted correctly
* Booking URL exists

FAIL if:
* No events found
* Missing city
* Missing date

### Devils Circuit

PASS if:
* Upcoming race cards extracted
* City names captured
* Registration URL extracted

FAIL if:
* Empty event list
* Invalid links

### Yodhaa Race

PASS if:
* All city race cards extracted
* Dates extracted
* Ticket links extracted

FAIL if:
* Missing city/date combinations

### Aggregation

PASS if:
* Events from all sources combined
* Duplicate entries removed

FAIL if:
* Duplicate events present
* Schema mismatch

---

# Phase 2 — Normalization Layer

## Goal

Convert all organizer-specific formats into one common structure.

## Deliverables

normalizer.py

Functions:
* normalize_hyrox()
* normalize_devils()
* normalize_yodhaa()

Unified output dataset.

---

## Validation Rules

Every event must contain:
* organizer
* city
* event_name
* booking_url
* start_date

Optional:
* venue
* end_date

---

## Test Cases

PASS if:
* All events match schema
* Dates converted to standard format
* Missing fields handled gracefully

FAIL if:
* Different schemas appear in output

---

# Phase 3 — Backend API

## Goal

Expose normalized event data through REST APIs.

## Deliverables

### GET /events

Returns all events.

### GET /events?city=Mumbai

Returns city-filtered events.

### GET /events?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

Returns date-filtered events.

### GET /status

Returns scraper health information.

---

## Example Status Response

```json
{
  "hyrox": "healthy",
  "devils_circuit": "healthy",
  "yodhaa": "healthy",
  "last_refresh": "2026-06-09T12:00:00"
}
```

---

## Test Cases

PASS if:
* APIs return HTTP 200
* City filtering works
* Date filtering works
* Status endpoint works

FAIL if:
* Incorrect filtering
* Empty responses despite valid data

---

# Phase 4 — Discovery Dashboard

## Design Direction
Developer-style dark dashboard.
- Dark background (#0f1117 or similar)
- Monospace or clean sans-serif
- Card-based event feed
- Status indicators (green dot = healthy)

## Components

### EventCard
Props: organizer, event_name, city, venue, start_date, end_date, booking_url
- Organizer badge (color-coded per brand)
- Date formatted as "17–20 Sep 2026"
- City + venue line
- Book Now → opens booking_url in new tab

### CityFilter
- Multi-select pill grid OR searchable dropdown
- Options: Mumbai, Bengaluru, Delhi NCR, Ahmedabad, Chandigarh, Hyderabad
- "All Cities" default

### DateRangePicker
- Library: react-day-picker or react-datepicker
- Clears independently of city filter
- Default: today → +12 months

### StatusBar
- Fetches /status endpoint
- Shows per-source health + last refresh time
- Top of dashboard, always visible

### EventFeed
- Applies city + date filters
- Empty state: "No races found for selected filters"
- Loading state: skeleton cards
- Error state: "Could not load events — showing cached data"

## API Integration
- lib/api.ts → fetchEvents(city?, startDate?, endDate?)
- Calls GET /events with query params
- SWR or useEffect + useState, refresh every 5 min client-side

## State
- selectedCities: string[]
- dateRange: { start: Date | null, end: Date | null }
- Filtering happens client-side after full fetch OR via API params (pick one, document it)

# Phase 5 — Data Refresh & Reliability

## Goal

Keep event information updated automatically.

## Deliverables

APScheduler-based refresh job.

Refresh frequency:

Every 4 hours.

Workflow:

Scrape Sources
↓
Normalize
↓
Update events.json
↓
Update API

---

## Test Cases

PASS if:
* Scheduler executes successfully
* Data refreshes automatically
* Last updated timestamp changes

FAIL if:
* Scheduler crashes
* Dataset not refreshed

---

# Phase 6 — Documentation & AI Workflow

## Goal

Demonstrate effective AI-assisted engineering.

## Deliverables

README.md
PROMPTING.md
Deployment instructions
Architecture overview

Known limitations

---

## PROMPTING.md Requirements

For each milestone:
1. Initial Prompt
2. AI Response
3. Error / Hallucination Encountered
4. Follow-up Prompt
5. Final Resolution

Examples:
* Scraper Architecture
* Dynamic Rendering Issues
* Frontend Filter Logic
* API Design
* Deployment

---

# Acceptance Criteria

Project will be considered complete when:

✓ HYROX events are extracted
✓ Devils Circuit events are extracted
✓ Yodhaa events are extracted
✓ Data normalized successfully
✓ API endpoints functional
✓ City filtering functional
✓ Date filtering functional
✓ Booking redirects functional
✓ Automatic refresh functional
✓ README completed
✓ PROMPTING.md completed
✓ Repository publicly accessible
✓ Application deployable from documentation

---

# Future Improvements (Out of Scope)

* PostgreSQL persistence
* User accounts
* Notifications
* Email alerts
* Event recommendation engine
* AI-powered race suggestions
* Historical race analytics

These are intentionally excluded to keep the scope focused on reliable event aggregation and discovery.