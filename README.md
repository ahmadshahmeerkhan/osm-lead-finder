# 📍 Lead Finder: Ethical Business Data & Contact Pipeline

An asynchronous Python pipeline built to discover local business entities using **OpenStreetMap (Overpass & Nominatim APIs)** and extract public contact information while strictly complying with web crawling ethics and domain-level policies.

---

## 📌 Overview

Traditional web scraping scripts often rely on anti-bot workarounds or third-party scraping services. This project takes an ethical, open-source approach:
1. It queries **OpenStreetMap's public spatial databases** to find registered businesses, addresses, phone numbers, and web domains.
2. It parses target websites exclusively for publicly listed email addresses while respecting each site's `robots.txt` rules and enforcing strict request throttling.

---

## 🛠️ Tech Stack & Architecture

| Component | Library / API | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core runtime environment |
| **Geocoding** | Nominatim API | Converts city strings to spatial bounding boxes |
| **Data Query** | Overpass API | Retrieves structured business nodes and metadata |
| **HTTP Engine** | `httpx` | Asynchronous HTTP requests with connection pooling |
| **HTML Parsing** | `BeautifulSoup4` + `lxml` | DOM traversing and email regex extraction |
| **Robots Compliance** | `urllib.robotparser` | Verifies target domain fetch permissions dynamically |

---

## 📊 Output Data Schema

Data is saved incrementally to `leads.csv`. Below is the exact structure of the generated CSV file:

| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `niche` | String | Target business category | `beauty salon` |
| `city` | String | Target location query | `Multan, Pakistan` |
| `business_name` | String | Verified name of the business | `Glow & Grace Salon` |
| `phone` | String | Listed primary contact phone number | `+92 300 1234567` |
| `website` | String | Official business web domain | `https://example.com` |
| `email` | String | Scraped public contact email address | `info@example.com` |
| `address` | String | Physical address registered on OSM | `Main Boulevard, Gulberg` |
| `osm_url` | String | Direct link to OpenStreetMap node | `https://www.openstreetmap.org/node/12345` |

---

## ⚙️ Configuration & Customization

You can target **any business category or geographic location** worldwide by editing the configuration variables inside `lead_scraper.py`.

### 1. Mapping OpenStreetMap Tags
OpenStreetMap categorizes entities using key-value tags (e.g., `shop`, `amenity`, `office`, `leisure`). You can add any category to `NICHE_TAGS`:

```python
# Configure OSM tag filters
NICHE_TAGS = {
    # Services & Beauty
    "beauty salon": '["shop"="beauty"]',
    "spa": '["leisure"="spa"]',
    "hair salon": '["shop"="hairdresser"]',
    
    # Food & Hospitality
    "restaurant": '["amenity"="restaurant"]',
    "cafe": '["amenity"="cafe"]',
    
    # Tech & Offices
    "software agency": '["office"="it"]',
    "real estate": '["office"="estate_agent"]',
}

# Select active targets for the run
NICHES = ["beauty salon", "spa"]
CITIES = ["Multan, Pakistan", "Lahore, Pakistan"]
