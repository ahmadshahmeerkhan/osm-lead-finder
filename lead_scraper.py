"""
Lead Finder — Business contact extractor using OpenStreetMap API & web parsing.
"""

import asyncio
import csv
import logging
import re
import urllib.robotparser
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

# --- Configuration ---

NICHE_TAGS = {
    "beauty salon": '["shop"="beauty"]',
    "spa": '["leisure"="spa"]',
    "hair salon": '["shop"="hairdresser"]',
    "car wrap / detailing": '["shop"="car_repair"]',
    "cafe": '["amenity"="cafe"]',
    "restaurant": '["amenity"="restaurant"]',
}

NICHES = ["cafe", "restaurant"]
CITIES = ["London, United Kingdom", "New York, USA"]

OUTPUT_FILE = "leads.csv"
MAX_RESULTS_PER_QUERY = 25
CONCURRENCY = 3
REQUEST_TIMEOUT = 15
MIN_DELAY_BETWEEN_REQUESTS = 1.5

USER_AGENT = "LeadFinder/1.0 (+https://github.com/ahmadshahmeerkhan)"

# --- Data Model ---

@dataclass
class Lead:
    niche: str
    city: str
    business_name: str
    phone: str
    website: str
    email: str
    address: str
    osm_url: str

    def to_dict(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}

# --- Setup ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Helper Functions ---

def extract_emails(text: str) -> list[str]:
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    found = re.findall(pattern, text)
    return [
        e for e in found
        if not re.search(r"\.(png|jpg|jpeg|gif|svg|webp|css|js)$", e, re.I)
    ]

def find_contact_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = a.get_text(strip=True).lower()
        if any(kw in href or kw in text for kw in ["contact", "about", "reach", "connect", "get-in-touch"]):
            full = href if href.startswith("http") else base_url.rstrip("/") + "/" + href.lstrip("/")
            candidates.append(full)
    return list(dict.fromkeys(candidates))[:3]

async def is_scraping_allowed(url: str, client: httpx.AsyncClient) -> bool:
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = await client.get(robots_url, timeout=8)
        if resp.status_code != 200:
            return True
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(resp.text.splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True

# --- API Queries ---

async def geocode_city(client: httpx.AsyncClient, city: str) -> Optional[tuple[float, float, float, float]]:
    params = {"q": city, "format": "json", "limit": 1}
    resp = await client.get(
        "https://nominatim.openstreetmap.org/search",
        params=params,
        headers={"User-Agent": USER_AGENT},
    )
    data = resp.json()
    if not data:
        log.warning(f"Could not geocode city: {city}")
        return None
    bbox = data[0]["boundingbox"]
    return tuple(float(x) for x in bbox)

async def query_overpass(client: httpx.AsyncClient, niche: str, bbox: tuple) -> list[dict]:
    tag_filter = NICHE_TAGS.get(niche)
    if not tag_filter:
        log.warning(f"No OSM tag mapping for niche '{niche}' — skipping.")
        return []

    south, north, west, east = bbox
    query = f"""
    [out:json][timeout:25];
    (
      node{tag_filter}({south},{west},{north},{east});
      way{tag_filter}({south},{west},{north},{east});
    );
    out center {MAX_RESULTS_PER_QUERY};
    """

    resp = await client.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    results = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        website = tags.get("website") or tags.get("contact:website") or ""
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        addr_parts = [
            tags.get("addr:housenumber", ""),
            tags.get("addr:street", ""),
            tags.get("addr:city", ""),
        ]
        address = " ".join(p for p in addr_parts if p)
        osm_id = el.get("id")
        osm_type = el.get("type")

        results.append({
            "name": name,
            "phone": phone,
            "website": website,
            "address": address,
            "osm_url": f"https://www.openstreetmap.org/{osm_type}/{osm_id}",
        })

    return results

# --- Web Parser ---

async def find_public_email(url: str, client: httpx.AsyncClient) -> Optional[str]:
    if not url:
        return None

    if not await is_scraping_allowed(url, client):
        log.info(f"robots.txt disallows checking {url} — skipping.")
        return None

    try:
        r = await client.get(url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
            raw = a["href"].replace("mailto:", "").split("?")[0].strip()
            if raw and "@" in raw:
                return raw

        emails = extract_emails(soup.get_text())
        if emails:
            return emails[0]

        base = f"{r.url.scheme}://{r.url.host}"
        for contact_url in find_contact_links(soup, base):
            await asyncio.sleep(MIN_DELAY_BETWEEN_REQUESTS)
            if not await is_scraping_allowed(contact_url, client):
                continue
            try:
                cr = await client.get(contact_url, timeout=REQUEST_TIMEOUT)
                csoup = BeautifulSoup(cr.text, "lxml")
                for a in csoup.find_all("a", href=re.compile(r"^mailto:", re.I)):
                    raw = a["href"].replace("mailto:", "").split("?")[0].strip()
                    if raw and "@" in raw:
                        return raw
                emails = extract_emails(csoup.get_text())
                if emails:
                    return emails[0]
            except Exception:
                continue

    except Exception as e:
        log.debug(f"Could not check {url}: {e}")

    return None

# --- CSV Handling ---

def init_csv(path: str):
    p = Path(path)
    if not p.exists():
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[f.name for f in fields(Lead)])
            writer.writeheader()

def append_lead_to_csv(lead: Lead, path: str):
    existing = []
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            existing = [r.get("business_name", "").strip() for r in csv.DictReader(f)]
    if lead.business_name.strip() in existing:
        log.info(f"Skipping duplicate: {lead.business_name}")
        return
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[f.name for f in fields(Lead)])
        writer.writerow(lead.to_dict())

# --- Core Runner ---

async def process_niche_city(client: httpx.AsyncClient, niche: str, city: str, semaphore: asyncio.Semaphore):
    bbox = await geocode_city(client, city)
    await asyncio.sleep(1)
    if not bbox:
        return

    businesses = await query_overpass(client, niche, bbox)
    log.info(f"'{niche}' in '{city}': found {len(businesses)} businesses via OpenStreetMap")

    async def handle_business(biz: dict):
        email = None
        if biz["website"]:
            async with semaphore:
                await asyncio.sleep(MIN_DELAY_BETWEEN_REQUESTS)
                email = await find_public_email(biz["website"], client)

        lead = Lead(
            niche=niche,
            city=city,
            business_name=biz["name"],
            phone=biz["phone"],
            website=biz["website"],
            email=email or "",
            address=biz["address"],
            osm_url=biz["osm_url"],
        )
        append_lead_to_csv(lead, OUTPUT_FILE)
        log.info(f"Saved: {lead.business_name} | email: {lead.email or 'none'}")

    for biz in businesses:
        await handle_business(biz)

async def main():
    init_csv(OUTPUT_FILE)
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
        for niche in NICHES:
            for city in CITIES:
                await process_niche_city(client, niche, city, semaphore)
                await asyncio.sleep(2)

    log.info(f"Done. Output saved to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    asyncio.run(main())
