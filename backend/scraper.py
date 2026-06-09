import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_hyrox():
    logger.info("Scraping HYROX India...")
    events = []
    base_url = "https://hyrox.co.in"
    find_race_url = f"{base_url}/find-my-race/"
    
    try:
        r = requests.get(find_race_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for local event page links e.g. /event/hyrox-mumbai/
        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/event/" in href and not href.endswith("/event/"):
                # Clean URL
                full_url = urllib.parse.urljoin(base_url, href)
                if not full_url.endswith("/"):
                    full_url += "/"
                event_links.add(full_url)
                
        logger.info(f"Found {len(event_links)} HYROX event pages: {event_links}")
        
        for url in event_links:
            try:
                logger.info(f"Fetching HYROX event details: {url}")
                er = requests.get(url, headers=HEADERS, timeout=10)
                er.raise_for_status()
                esoup = BeautifulSoup(er.text, 'html.parser')
                
                # Title
                title = esoup.title.string.strip() if esoup.title else ""
                title = title.split("|")[0].strip() # Clean WordPress title
                
                # Check for BUY TICKETS link
                booking_url = None
                for ea in esoup.find_all('a', href=True):
                    ehref = ea['href']
                    etext = ea.get_text(strip=True).upper()
                    if "BUY TICKETS" in etext or "india.hyrox.co.in/event" in ehref:
                        booking_url = ehref
                        break
                
                # If booking link not found, default to finding any india.hyrox link
                if not booking_url:
                    for ea in esoup.find_all('a', href=True):
                        if "india.hyrox.co.in" in ea['href']:
                            booking_url = ea['href']
                            break
                            
                # Locate dates
                # In WP page, dates are usually in headers or paragraphs. Let's extract date strings from the text
                # We can also parse from the event page content.
                # E.g. "Masters' Union HYROX Delhi" has "24. Jul. 2026" / "26. Jul. 2026"
                body_text = esoup.get_text()
                # Find date matches like "24. Jul. 2026" or "17. Sep. 2026"
                dates = re.findall(r'\d{1,2}\.\s+[A-Za-z]{3}\.\s+\d{4}', body_text)
                
                # Standard fallback or direct parse
                # Let's clean up title to extract city
                city = "India"
                if "delhi" in url.lower():
                    city = "Delhi NCR"
                elif "mumbai" in url.lower():
                    city = "Mumbai"
                
                start_date = None
                end_date = None
                if dates:
                    # Sort matches chronologically if possible, or take first as start, last as end
                    # The dates found: e.g. ['24. Jul. 2026', '26. Jul. 2026']
                    start_date = dates[0]
                    if len(dates) > 1:
                        end_date = dates[1]
                
                # If no dates found in body, parse from title or fallback
                # e.g., Delhi is July 24-26, 2026; Mumbai is September 17-20, 2026
                # We can have a hardcoded fallback mapping if regex fails
                if not start_date:
                    if "delhi" in url.lower():
                        start_date = "24. Jul. 2026"
                        end_date = "26. Jul. 2026"
                    elif "mumbai" in url.lower():
                        start_date = "17. Sep. 2026"
                        end_date = "20. Sep. 2026"
                
                events.append({
                    "organizer": "HYROX",
                    "event_name": title or f"HYROX {city}",
                    "city": city,
                    "venue": "NESCO Centre" if "mumbai" in url.lower() else "Yashobhoomi (IICC)" if "delhi" in url.lower() else None,
                    "start_date_raw": start_date,
                    "end_date_raw": end_date,
                    "booking_url": booking_url or url,
                    "source_url": url
                })
                logger.info(f"Successfully scraped HYROX event: {city}")
            except Exception as ex:
                logger.error(f"Error scraping individual HYROX page {url}: {ex}")
                
    except Exception as e:
        logger.error(f"Error scraping HYROX find-my-race: {e}")
        
    return events

def scrape_devils_circuit():
    logger.info("Scraping Devils Circuit...")
    events = []
    base_url = "https://www.devilscircuit.com"
    
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        # Find index.js chunk
        m = re.search(r'/_next/static/chunks/pages/index-[a-f0-9]+\.js', r.text)
        if not m:
            logger.error("Could not find Devils Circuit index.js chunk in HTML!")
            return events
            
        js_url = base_url + m.group(0)
        logger.info(f"Found Devils Circuit JS URL: {js_url}")
        
        js_r = requests.get(js_url, headers=HEADERS, timeout=10)
        js_r.raise_for_status()
        
        # Find all event objects in the array
        # Format: {name:"Chandigarh",image:"...",date:"September 13, 2026",registrationLink:"https://..."}
        # Keys might have quotes or not, values have quotes. Let's use regex that handles both.
        matches = re.findall(
            r'\{\s*name\s*:\s*"(.*?)",\s*image\s*:\s*"(.*?)",\s*date\s*:\s*"(.*?)",\s*registrationLink\s*:\s*"(.*?)"\s*\}',
            js_r.text
        )
        
        for name, image, date_str, reg_link in matches:
            events.append({
                "organizer": "Devils Circuit",
                "event_name": f"Maruti Suzuki Arena Devils Circuit {name}",
                "city": name,
                "venue": None,
                "start_date_raw": date_str,
                "end_date_raw": None,
                "booking_url": reg_link,
                "source_url": base_url
            })
            
        logger.info(f"Successfully scraped {len(events)} events from Devils Circuit.")
    except Exception as e:
        logger.error(f"Error scraping Devils Circuit: {e}")
        
    return events

def scrape_yodhaa():
    logger.info("Scraping The Yodhaa Race...")
    events = []
    base_url = "https://theyoddharace.com"
    find_race_url = f"{base_url}/find-race"
    
    try:
        r = requests.get(find_race_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        
        # Find all script chunks in HTML
        chunks = re.findall(r'/_next/static/chunks/[a-f0-9A-Za-z_-]+\.js', r.text)
        logger.info(f"Found {len(chunks)} JS chunks on Yodhaa find-race page.")
        
        for chunk in chunks:
            js_url = base_url + chunk
            try:
                js_r = requests.get(js_url, headers=HEADERS, timeout=10)
                js_r.raise_for_status()
                
                # Check if this script chunk has the events array
                # Format: {name:"MUMBAI",date:"21st-22nd Nov 2026",eventDateISO:"2026-11-21T00:00:00+05:30",link:"https://..."}
                matches = re.findall(
                    r'\{\s*name\s*:\s*"(.*?)",\s*date\s*:\s*"(.*?)",\s*eventDateISO\s*:\s*"(.*?)",\s*link\s*:\s*"(.*?)"\s*\}',
                    js_r.text
                )
                
                if matches:
                    logger.info(f"Found event array in chunk {chunk} with {len(matches)} events.")
                    for name, date_str, date_iso, link in matches:
                        events.append({
                            "organizer": "The Yodhaa Race",
                            "event_name": f"The Yoddha Race {name.title()}",
                            "city": name.title(),
                            "venue": None,
                            "start_date_raw": date_iso, # We can use the ISO string directly!
                            "end_date_raw": None,
                            "booking_url": link,
                            "source_url": find_race_url
                        })
                    break # Found the chunk, no need to process other chunks
            except Exception as chunk_ex:
                # Silently ignore individual chunk errors unless it's critical
                pass
                
        logger.info(f"Successfully scraped {len(events)} events from Yodhaa.")
    except Exception as e:
        logger.error(f"Error scraping Yodhaa Race: {e}")
        
    return events

def scrape_all():
    logger.info("Starting combined scrape...")
    all_events = []
    
    hyrox = scrape_hyrox()
    all_events.extend(hyrox)
    
    devils = scrape_devils_circuit()
    all_events.extend(devils)
    
    yodhaa = scrape_yodhaa()
    all_events.extend(yodhaa)
    
    logger.info(f"Scraped total of {len(all_events)} events.")
    return all_events

if __name__ == "__main__":
    import json
    print("Testing scrapers...")
    data = scrape_all()
    print(json.dumps(data, indent=2))
