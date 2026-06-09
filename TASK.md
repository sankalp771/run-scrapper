This is actual task provided to me :
Overview
Fitness racing and obstacle course racing (OCR) are exploding in India, but the event data is highly fragmented across different organizer sites. Your task is to build a web application called "Vibe Race Tracker India" that automatically aggregates, filters, and redirects users to upcoming major fitness races across the country (such as HYROX India, Devils Circuit, and The Yodhaa Race).
We care less about you manually writing every line of boilerplate code by hand and more about how fast and effectively you steer AI harnesses (Cursor, Claude, Codex) to engineer a working, high-quality, full-stack product.
🛠️ The Tech Stack
Frontend: React / Next.js
Backend: Python 
🎯 Core Requirements
1. The Scraping & Normalization Engine (Backend)
Your application must programmatically extract upcoming event details directly of the following live platforms:
HYROX India (india.hyrox.co.in or their ticketing platform widget)
Maruti Suzuki Arena Devils Circuit (devilscircuit.com)
The Yodhaa Race (theyoddharace.com)
2. The Discovery Dashboard (Frontend)
Build a clean, high-fidelity developer-style dashboard to display this live data:
Race Feed: Display the upcoming events as visually distinct, responsive layout cards. Each card must feature the organizer's name, race specifications, localized date/city, and a prominent call-to-action button.
City Filter: A searchable dropdown or selection grid allowing users to filter races by specific Indian cities (e.g., Mumbai, Bengaluru, Delhi NCR).
Date Range Picker: An interactive calendar or range filter that dynamically displays events falling within selected dates.
Booking Redirect: Clicking the "Book Now" CTA on any race card must securely open a new tab redirecting the user straight to that race's official registration or checkout page.
🚀 AI Tooling & Documentation Requirements (Crucial)
Because we expect you to leverage state-of-the-art AI coding tools to accelerate your workflow, your submission will be heavily evaluated on how you direct the AI and pivot when it encounters errors.
Maintain a PROMPTING.md file: Create this file in the root of your repository.
Document the Evolutionary Steps: For core milestones (e.g., setting up the scraper architecture, resolving headless rendering blocks, or building the frontend calendar range logic), log:
The initial prompt you provided.
Any AI hallucinations, outdated boilerplate, or errors that broke your app.
The follow-up prompts you used to guide the AI to correct its mistake.
Share Links: If you utilized web-based interfaces (like ChatGPT or Claude), paste the public share links of those chats at the top of your PROMPTING.md file.
📤 Submission Checklist
When complete, please reply with:
The link to your public GitHub repository (containing your application source code, a README.md with setup steps, and your PROMPTING.md file).