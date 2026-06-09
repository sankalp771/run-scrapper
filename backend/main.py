from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone
import json
import os
import logging
from contextlib import asynccontextmanager

from scraper import scrape_hyrox, scrape_devils_circuit, scrape_yodhaa
from normalizer import normalize_all, EventSchema

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EVENTS_FILE = "backend/events.json"
STATUS_FILE = "backend/status.json"

def read_json_file(filepath: str, default: Any) -> Any:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
    return default

def write_json_file(filepath: str, data: Any):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error writing to file {filepath}: {e}")

def run_scrapers_and_update():
    logger.info("Executing background scraping job...")
    status = {
        "hyrox": "healthy",
        "devils_circuit": "healthy",
        "yodhaa": "healthy",
        "last_refresh": datetime.now(timezone.utc).isoformat()
    }
    
    raw_events = []
    
    # 1. Scrape HYROX
    try:
        hyrox_events = scrape_hyrox()
        raw_events.extend(hyrox_events)
        if not hyrox_events:
            status["hyrox"] = "no_events_found"
    except Exception as e:
        logger.error(f"HYROX scraping failed: {e}")
        status["hyrox"] = "failed"
        
    # 2. Scrape Devils Circuit
    try:
        devils_events = scrape_devils_circuit()
        raw_events.extend(devils_events)
        if not devils_events:
            status["devils_circuit"] = "no_events_found"
    except Exception as e:
        logger.error(f"Devils Circuit scraping failed: {e}")
        status["devils_circuit"] = "failed"
        
    # 3. Scrape Yodhaa
    try:
        yodhaa_events = scrape_yodhaa()
        raw_events.extend(yodhaa_events)
        if not yodhaa_events:
            status["yodhaa"] = "no_events_found"
    except Exception as e:
        logger.error(f"Yodhaa scraping failed: {e}")
        status["yodhaa"] = "failed"
        
    # Normalize and save
    normalized = normalize_all(raw_events)
    # Convert schemas to dictionaries for storage
    events_data = [event.model_dump() for event in normalized]
    
    write_json_file(EVENTS_FILE, events_data)
    write_json_file(STATUS_FILE, status)
    logger.info(f"Scrape cycle complete. Saved {len(events_data)} normalized events.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from apscheduler.schedulers.background import BackgroundScheduler
    
    # Setup background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scrapers_and_update, 'interval', hours=4)
    scheduler.start()
    logger.info("Started background scheduler for scraping every 4 hours.")
    
    # Startup: Always run initial scrape on startup to populate live events
    logger.info("Running initial scrape on startup...")
    try:
        run_scrapers_and_update()
    except Exception as e:
        logger.error(f"Failed to run initial scrape on startup: {e}")
        
    yield
    
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("Stopped background scheduler.")

app = FastAPI(
    title="Vibe Race Tracker India API",
    description="Provides aggregated fitness race events from HYROX, Devils Circuit, and Yodhaa Race.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # NextJS frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to Vibe Race Tracker India API. Use /events to retrieve races, /status for scraper details, or /refresh to force updates."
    }

@app.get("/events", response_model=List[EventSchema])
def get_events(
    city: Optional[str] = Query(None, description="Filter races by Indian city (case-insensitive)"),
    start_date: Optional[str] = Query(None, description="Start of date range filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End of date range filter (YYYY-MM-DD)")
):
    events = read_json_file(EVENTS_FILE, [])
    filtered = events
    
    if city:
        city_lower = city.lower().strip()
        filtered = [e for e in filtered if e["city"].lower() == city_lower]
        
    if start_date:
        try:
            limit = date.fromisoformat(start_date)
            filtered = [e for e in filtered if date.fromisoformat(e["start_date"]) >= limit]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD.")
            
    if end_date:
        try:
            limit = date.fromisoformat(end_date)
            filtered = [e for e in filtered if date.fromisoformat(e["start_date"]) <= limit]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD.")
            
    # Convert dictionaries to EventSchema models
    try:
        return [EventSchema(**e) for e in filtered]
    except Exception as e:
        logger.error(f"Error parsing events from storage: {e}")
        raise HTTPException(status_code=500, detail="Stored event data did not match schema validation.")

@app.get("/status")
def get_status():
    status = read_json_file(STATUS_FILE, {
        "hyrox": "unknown",
        "devils_circuit": "unknown",
        "yodhaa": "unknown",
        "last_refresh": None
    })
    return status

@app.post("/refresh")
def force_refresh():
    try:
        run_scrapers_and_update()
        return {"status": "success", "message": "Scraper executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
