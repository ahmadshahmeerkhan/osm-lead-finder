# 📍 Lead Finder: Ethical Business Data & Contact Pipeline

An asynchronous Python tool designed to locate businesses using OpenStreetMap APIs (Overpass & Nominatim) and extract public contact information while respecting site permissions and API policies.

---

## Features

* **Open API Business Discovery:** Retrieves business locations and details directly from OpenStreetMap's Overpass API.
* **Robots.txt Checking:** Verifies scraping permission using Python's native `urllib.robotparser` before checking any external website.
* **Polite Asynchronous Requests:** Manages request rates and limits concurrent connections using `httpx` and `asyncio.Semaphore`.
* **Contact Discovery:** Scrapes email addresses from homepage metadata, `mailto:` links, or linked `/contact` pages.
* **CSV Export:** Saves leads iteratively while skipping duplicates automatically.

---

## Architecture Flow

1. **Geocoding:** Converts target city names to bounding boxes via Nominatim API.
2. **Data Query:** Requests matching nodes/ways from the Overpass API using structured OSM tags.
3. **Permission Check:** Checks target domain `robots.txt` policy.
4. **Parsing:** Parses public contact details using `httpx` and `BeautifulSoup4`.
5. **Output:** Formats and appends unique records directly to `leads.csv`.

---

## Requirements

* Python 3.10+
* Dependencies:
  * `httpx`
  * `beautifulsoup4`
  * `lxml`

---

## Setup & Execution

1. Clone the repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/osm-lead-finder.git](https://github.com/YOUR_USERNAME/osm-lead-finder.git)
   cd osm-lead-finder
