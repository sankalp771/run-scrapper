"use client";

import { useEffect, useState } from "react";

interface Event {
  id: string;
  organizer: string;
  event_name: string;
  city: string;
  venue: string | null;
  start_date: string;
  end_date: string | null;
  booking_url: string;
  ticket_url: string | null;
  source_url: string;
  last_updated: string;
}

interface ScraperStatus {
  hyrox: string;
  devils_circuit: string;
  yodhaa: string;
  last_refresh: string | null;
}

const CITIES = [
  "All Cities",
  "Delhi NCR",
  "Mumbai",
  "Bengaluru",
  "Hyderabad",
  "Chandigarh",
  "Ahmedabad",
  "Pune",
  "Indore",
  "Jaipur",
  "Kochi",
  "Chennai",
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function DashboardPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [status, setStatus] = useState<ScraperStatus>({
    hyrox: "unknown",
    devils_circuit: "unknown",
    yodhaa: "unknown",
    last_refresh: null
  });
  
  const [selectedCity, setSelectedCity] = useState("All Cities");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch scraper status once on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/status`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch scraper status");
        return res.json();
      })
      .then((data) => setStatus(data))
      .catch((err) => console.error("Error fetching status:", err));
  }, []);

  // Fetch events on filter change
  useEffect(() => {
    setLoading(true);
    setError(null);

    let queryParams = [];
    if (selectedCity !== "All Cities") {
      queryParams.push(`city=${encodeURIComponent(selectedCity)}`);
    }
    if (startDate) {
      queryParams.push(`start_date=${startDate}`);
    }
    if (endDate) {
      queryParams.push(`end_date=${endDate}`);
    }

    const queryString = queryParams.length > 0 ? `?${queryParams.join("&")}` : "";
    
    fetch(`${API_BASE_URL}/events${queryString}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch events from server");
        return res.json();
      })
      .then((data) => {
        setEvents(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [selectedCity, startDate, endDate]);

  const clearFilters = () => {
    setSelectedCity("All Cities");
    setStartDate("");
    setEndDate("");
  };

  const formatEventDate = (startStr: string, endStr: string | null) => {
    const start = new Date(startStr);
    const options: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" };
    
    if (!endStr) {
      return start.toLocaleDateString("en-IN", options);
    }
    
    const end = new Date(endStr);
    if (start.getMonth() === end.getMonth()) {
      return `${start.getDate()}–${end.getDate()} ${start.toLocaleDateString("en-IN", { month: "short", year: "numeric" })}`;
    }
    
    return `${start.toLocaleDateString("en-IN", { day: "numeric", month: "short" })} – ${end.toLocaleDateString("en-IN", options)}`;
  };

  const formatLastSync = (isoString: string | null) => {
    if (!isoString) return "Never";
    const d = new Date(isoString);
    return d.toLocaleString("en-IN", { 
      hour: "2-digit", 
      minute: "2-digit", 
      second: "2-digit",
      day: "numeric", 
      month: "short"
    });
  };

  const getCardClass = (org: string) => {
    if (org.toLowerCase().includes("hyrox")) return "event-card hyrox";
    if (org.toLowerCase().includes("devils")) return "event-card devils";
    return "event-card yodhaa";
  };

  return (
    <div className="dashboard-container">
      {/* Title */}
      <header className="dashboard-header">
        <div className="title-area">
          <h1>Vibe Race Tracker India</h1>
          <p>India's ultimate fitness & obstacle racing calendar feed</p>
        </div>
        
        {/* Status Bar */}
        <div className="status-bar" id="status-bar">
          <div className="status-item">
            <span className="status-label">HYROX:</span>
            <span className={`status-dot ${status.hyrox}`}></span>
            <span className="status-value">{status.hyrox.toUpperCase()}</span>
          </div>
          <div className="status-item">
            <span className="status-label">Devils Circuit:</span>
            <span className={`status-dot ${status.devils_circuit}`}></span>
            <span className="status-value">{status.devils_circuit.toUpperCase()}</span>
          </div>
          <div className="status-item">
            <span className="status-label">Yodhaa Race:</span>
            <span className={`status-dot ${status.yodhaa}`}></span>
            <span className="status-value">{status.yodhaa.toUpperCase()}</span>
          </div>
          <div className="last-sync">
            Synced: {formatLastSync(status.last_refresh)}
          </div>
        </div>
      </header>

      {/* Filters */}
      <section className="filter-panel">
        <div className="filter-section">
          <h2 className="filter-title">Filter by City</h2>
          <div className="city-grid">
            {CITIES.map((city) => (
              <button
                key={city}
                id={`city-filter-${city.toLowerCase().replace(/\s+/g, "-")}`}
                className={`city-pill ${selectedCity === city ? "active" : ""}`}
                onClick={() => setSelectedCity(city)}
              >
                {city}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-section">
          <h2 className="filter-title">Filter by Date Range</h2>
          <div className="date-inputs">
            <div className="date-input-wrapper">
              <input
                type="date"
                id="start-date-picker"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                aria-label="Start date"
              />
            </div>
            <span className="date-separator">to</span>
            <div className="date-input-wrapper">
              <input
                type="date"
                id="end-date-picker"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                aria-label="End date"
              />
            </div>
            {(selectedCity !== "All Cities" || startDate || endDate) && (
              <button className="clear-btn" onClick={clearFilters}>
                Clear
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Feed Title */}
      <div className="feed-header">
        <h2>Upcoming Races</h2>
        <span className="event-count">{events.length} races found</span>
      </div>

      {/* Event List */}
      {loading ? (
        <div className="events-grid">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton-card"></div>
          ))}
        </div>
      ) : error ? (
        <div className="error-state">
          <h3>Error Loading Events</h3>
          <p>{error}</p>
          <button className="clear-btn" style={{ marginTop: "1rem" }} onClick={clearFilters}>
            Reset Filters
          </button>
        </div>
      ) : events.length === 0 ? (
        <div className="empty-state">
          <h3>No races found</h3>
          <p>Try adjusting your search criteria or date range.</p>
          <button className="clear-btn" style={{ marginTop: "1rem" }} onClick={clearFilters}>
            Clear All Filters
          </button>
        </div>
      ) : (
        <div className="events-grid">
          {events.map((event) => (
            <article key={event.id} className={getCardClass(event.organizer)}>
              <div className="card-header">
                <span className="organizer-badge">{event.organizer}</span>
                <span className="location-badge">{event.city}</span>
              </div>
              
              <div className="card-content">
                <h3 className="card-title">{event.event_name}</h3>
                
                <div className="card-details">
                  <div className="detail-item">
                    <svg className="detail-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>{formatEventDate(event.start_date, event.end_date)}</span>
                  </div>
                  
                  {event.venue && (
                    <div className="detail-item">
                      <svg className="detail-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span>{event.venue}</span>
                    </div>
                  )}
                </div>
              </div>

              <button
                id={`book-btn-${event.id}`}
                className="cta-button"
                onClick={() => window.open(event.booking_url, "_blank", "noopener,noreferrer")}
              >
                Book Now
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
