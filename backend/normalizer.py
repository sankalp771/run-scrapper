from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import re
import logging
import urllib.parse

logger = logging.getLogger(__name__)

class EventSchema(BaseModel):
    id: str
    organizer: str
    event_name: str
    city: str
    venue: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    booking_url: str
    ticket_url: Optional[str] = None
    source_url: str
    last_updated: datetime

CITY_MAP = {
    "delhi": "Delhi NCR",
    "delhi ncr": "Delhi NCR",
    "ncr": "Delhi NCR",
    "mumbai": "Mumbai",
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "hyderabad": "Hyderabad",
    "chandigarh": "Chandigarh",
    "ahmedabad": "Ahmedabad",
    "indore": "Indore",
    "jaipur": "Jaipur",
    "pune": "Pune",
    "kochi": "Kochi",
    "chennai": "Chennai",
    "kolkata": "Kolkata"
}

def normalize_city(city_raw: Optional[str]) -> str:
    if not city_raw:
        return "India"
    cleaned = city_raw.strip().lower()
    return CITY_MAP.get(cleaned, city_raw.strip())

def parse_date(date_str: str) -> date:
    if not date_str:
        raise ValueError("Empty date string")
        
    date_str = date_str.strip()
    
    # Check if standard YYYY-MM-DD format (from events.json serialization)
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        pass
        
    # Check if ISO format with time (e.g. 2026-11-21T00:00:00+05:30)
    if "T" in date_str:
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            pass
            
    # Check format: "24. Jul. 2026"
    try:
        cleaned = re.sub(r'\.', '', date_str) # remove dots
        return datetime.strptime(cleaned, "%d %b %Y").date()
    except ValueError:
        pass
        
    # Check format: "September 13, 2026"
    try:
        return datetime.strptime(date_str, "%B %d, %Y").date()
    except ValueError:
        pass
        
    # Check format: "September 13 2026" (no comma)
    try:
        return datetime.strptime(date_str, "%B %d %Y").date()
    except ValueError:
        pass
        
    # Fallback to match start day in range: "September 13-14, 2026"
    m = re.match(r'([A-Za-z]+)\s+(\d+)-\d+,\s+(\d{4})', date_str)
    if m:
        month, day, year = m.groups()
        try:
            return datetime.strptime(f"{month} {day}, {year}", "%B %d, %Y").date()
        except ValueError:
            pass

    raise ValueError(f"Unable to parse date string: {date_str}")

def parse_date_range(start_raw: Optional[str], end_raw: Optional[str]) -> tuple[date, Optional[date]]:
    if not start_raw:
        raise ValueError("Start date is required")
        
    # Standardize if we have a range in a single string (like "November 28-29, 2026")
    start_raw = start_raw.strip()
    m = re.match(r'([A-Za-z]+)\s+(\d+)-(\d+),\s+(\d{4})', start_raw)
    if m:
        month, day_start, day_end, year = m.groups()
        start = datetime.strptime(f"{month} {day_start}, {year}", "%B %d, %Y").date()
        end = datetime.strptime(f"{month} {day_end}, {year}", "%B %d, %Y").date()
        return start, end
        
    # Standardize if start_raw has "24. Jul. 2026" and end_raw has "26. Jul. 2026"
    start = parse_date(start_raw)
    end = None
    if end_raw:
        try:
            end = parse_date(end_raw)
        except Exception:
            pass
            
    return start, end

def build_unique_id(organizer: str, city: str, start_date: date) -> str:
    org_slug = organizer.lower().replace(" ", "_").replace("'", "")
    city_slug = city.lower().replace(" ", "_")
    return f"{org_slug}_{city_slug}_{start_date.isoformat()}"

def normalize_event(raw_event: Dict[str, Any], last_updated: datetime) -> Optional[EventSchema]:
    try:
        organizer = raw_event["organizer"]
        city = normalize_city(raw_event.get("city"))
        start_date, end_date = parse_date_range(raw_event.get("start_date_raw"), raw_event.get("end_date_raw"))
        event_id = build_unique_id(organizer, city, start_date)
        
        # Determine main booking (info) URL and direct ticket URL
        raw_booking = raw_event["booking_url"]
        raw_source = raw_event["source_url"]
        
        booking_url = raw_booking
        ticket_url = raw_booking
        
        if organizer == "Devils Circuit":
            booking_url = f"https://www.devilscircuit.com/city/{urllib.parse.quote(city)}"
            ticket_url = raw_booking
        elif organizer == "The Yodhaa Race":
            # Map Delhi NCR to Delhi for Yodhaa city page slug
            slug_city = "Delhi" if city == "Delhi NCR" else city
            booking_url = f"https://theyoddharace.com/city/{urllib.parse.quote(slug_city)}"
            ticket_url = raw_booking
        elif organizer == "HYROX":
            booking_url = raw_source  # The main WordPress info page
            ticket_url = raw_booking  # The direct vivenu booking widget
            
        normalized = EventSchema(
            id=event_id,
            organizer=organizer,
            event_name=raw_event["event_name"],
            city=city,
            venue=raw_event.get("venue"),
            start_date=start_date,
            end_date=end_date,
            booking_url=booking_url,
            ticket_url=ticket_url,
            source_url=raw_source,
            last_updated=last_updated
        )
        return normalized
    except Exception as e:
        logger.error(f"Failed to normalize raw event {raw_event}: {e}")
        return None

def diff_and_normalize(existing_events: List[Dict[str, Any]], raw_events: List[Dict[str, Any]]) -> List[EventSchema]:
    from datetime import timezone
    current_time = datetime.now(timezone.utc)
    
    # Map existing events by their unique ID
    existing_map = {e["id"]: e for e in existing_events}
    
    normalized_list = []
    seen_ids = set()
    
    for raw in raw_events:
        # Create a temporary normalization to compare fields
        temp_item = normalize_event(raw, current_time)
        if not temp_item:
            continue
            
        event_id = temp_item.id
        if event_id in seen_ids:
            continue
        seen_ids.add(event_id)
        
        # Compare with existing event in database
        if event_id in existing_map:
            existing = existing_map[event_id]
            
            # Check if any details have changed
            # Exclude last_updated from comparison
            end_date_existing = parse_date(str(existing["end_date"])) if existing.get("end_date") else None
            
            fields_changed = (
                existing.get("event_name") != temp_item.event_name or
                existing.get("city") != temp_item.city or
                existing.get("venue") != temp_item.venue or
                parse_date(str(existing["start_date"])) != temp_item.start_date or
                end_date_existing != temp_item.end_date or
                existing.get("booking_url") != temp_item.booking_url or
                existing.get("ticket_url") != temp_item.ticket_url or
                existing.get("source_url") != temp_item.source_url
            )
            
            if fields_changed:
                # Field changed: Update fields and reset updated timestamp
                temp_item.last_updated = current_time
                normalized_list.append(temp_item)
                logger.info(f"Event details changed for: {temp_item.event_name}. Updating database record.")
            else:
                # Keep existing record (preserve original last_updated timestamp)
                last_up_raw = existing.get("last_updated")
                if isinstance(last_up_raw, str):
                    last_up = datetime.fromisoformat(last_up_raw)
                else:
                    last_up = last_up_raw or current_time
                    
                existing_item = EventSchema(
                    id=event_id,
                    organizer=existing["organizer"],
                    event_name=existing["event_name"],
                    city=existing["city"],
                    venue=existing.get("venue"),
                    start_date=parse_date(str(existing["start_date"])),
                    end_date=end_date_existing,
                    booking_url=existing["booking_url"],
                    ticket_url=existing.get("ticket_url"),
                    source_url=existing["source_url"],
                    last_updated=last_up
                )
                normalized_list.append(existing_item)
        else:
            # New event discovered
            temp_item.last_updated = current_time
            normalized_list.append(temp_item)
            logger.info(f"New event discovered: {temp_item.event_name}. Adding to database.")
            
    # Any event in existing_map that was not in raw_events (not seen) is discarded,
    # satisfying the dynamic removal requirement.
    return normalized_list

def normalize_all(raw_events: List[Dict[str, Any]]) -> List[EventSchema]:
    from datetime import timezone
    normalized_list = []
    seen_ids = set()
    last_updated = datetime.now(timezone.utc)
    
    for raw in raw_events:
        item = normalize_event(raw, last_updated)
        if item and item.id not in seen_ids:
            seen_ids.add(item.id)
            normalized_list.append(item)
            
    return normalized_list

if __name__ == "__main__":
    # Test normalization
    test_raw = [
        {
            "organizer": "HYROX",
            "event_name": "Masters' Union HYROX Delhi",
            "city": "Delhi",
            "venue": "Yashobhoomi (IICC)",
            "start_date_raw": "24. Jul. 2026",
            "end_date_raw": "26. Jul. 2026",
            "booking_url": "https://india.hyrox.co.in/event/hyrox-delhi-season-26-27-xszluf",
            "source_url": "https://hyrox.co.in/event/hyrox-delhi/"
        },
        {
            "organizer": "Devils Circuit",
            "event_name": "Maruti Suzuki Arena Devils Circuit Mumbai",
            "city": "Mumbai",
            "venue": None,
            "start_date_raw": "November 28-29, 2026",
            "end_date_raw": None,
            "booking_url": "https://getmybib.com/281/category?ename=Maruti-Suzuki-Arena-Devils-Circuit-Mumbai-2026-27",
            "source_url": "https://www.devilscircuit.com"
        },
        {
            "organizer": "The Yodhaa Race",
            "event_name": "The Yoddha Race Hyderabad",
            "city": "Hyderabad",
            "venue": None,
            "start_date_raw": "2026-12-05T00:00:00+05:30",
            "end_date_raw": None,
            "booking_url": "https://getmybib.com/294/register?ename=S3:-The-Yoddha-Race---Hyderabad",
            "source_url": "https://theyoddharace.com/find-race"
        }
    ]
    
    results = normalize_all(test_raw)
    for r in results:
        print(r.model_dump_json(indent=2))