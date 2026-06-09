# Frontend Architectural Design Decisions & Reasoning

This document explains the technical choices, user experience details, and reasoning behind the implementation details of the Vibe Race Tracker India Next.js frontend.

---

## 1. Dynamic Cities Extraction on Page Mount

### The Challenge
Initially, the city filter panel featured a hardcoded list of major Indian cities (e.g., Delhi NCR, Mumbai, Bangalore, Jaipur, Kolkata).
However, if a user clicked on "Kolkata" or "Jaipur" when there were no upcoming races scraped for those cities, the UI would snap to a blank "No races found" empty state. This is an annoying user experience.

### Our Solution
We removed the hardcoded cities list from the frontend. The dashboard now fetches the events on mount and dynamically computes the unique list of cities:
```typescript
const uniqueCities = Array.from(new Set(data.map((e) => e.city)))
  .filter(Boolean)
  .sort();
setAvailableCities(["All Cities", ...uniqueCities]);
```

### The Reasoning
- **Zero Stale States**: Users only see city pills that *actually* contain upcoming events, preventing empty searches.
- **Auto-Expansion**: If a new race is scraped in a new city (e.g., Pune) tomorrow, it instantly appears in the selector bar without requiring any frontend code changes or redeployments.

---

## 2. API Portability via Environment Variables (`NEXT_PUBLIC_API_URL`)

### The Challenge
Hardcoding `http://127.0.0.1:8000` in the client code works locally but breaks in production when the Next.js app tries to contact the localhost of the user's browser rather than the deployed Render server.

### Our Solution
We configured Next.js to read the backend API URL dynamically from the environment:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
```

### The Reasoning
- Next.js requires environment variables accessed on the client-side to be prefixed with `NEXT_PUBLIC_` to prevent them from being hidden behind server-side compilation boundaries.
- Setting the fallback to `"http://127.0.0.1:8000"` ensures that developers can clone and run the project locally without setting up any `.env` files, keeping development setup simple and seamless.

---

## 3. Vanilla CSS Overrides on `react-datepicker`

### The Challenge
Native HTML5 `<input type="date">` inputs are styled differently in every browser (Chrome, Firefox, Safari) and look basic on mobile. We wanted a professional, custom calendar popover but didn't want to bring in a heavy UI framework (like Material UI or Radix).

### Our Solution
We installed the lightweight `react-datepicker` package, imported its basic structural stylesheet, and overrode its namespace classes (e.g. `.react-datepicker`, `.react-datepicker__header`, `.react-datepicker__day`) directly in `globals.css` using our design variables.

### The Reasoning
- **Design Consistency**: Overriding standard classes allows us to apply our carbon glassmorphism styling, Outfit fonts, glowing borders, and selection gradients to the popover.
- **Lightweight**: Avoids bloating the application bundle with large third-party components or styling libraries.

---

## 4. Independent Filter Resets

### Our Solution
We split the filter clearing logic into three separate actions:
- **`resetCityFilter`**: Clears only the city, keeping selected dates.
- **`clearDates`**: Resets start/end dates, keeping selected city.
- **`clearAllFilters`**: Global reset for empty or error states.

### The Reasoning
- Gives users granular control over their calendar search. A user looking for races in "Mumbai" shouldn't have their custom date ranges reset just because they wanted to see all cities, and vice versa.