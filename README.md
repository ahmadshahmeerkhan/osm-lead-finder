# 📍 Lead Finder

A small async Python pipeline that finds local businesses using OpenStreetMap and checks their websites for a public contact email. I built this while trying to find leads for an automation side-project idea I was testing.

## 💡 Why I built this

I wanted to try building small automation tools for local businesses, things like AI voice agents that could handle bookings for salons and spas. But before I could pitch anyone, I needed to actually find businesses to contact, and doing that manually (searching, copying info, writing outreach one at a time) took forever, maybe an hour just to get through a handful of leads.

The first version of this used Google Maps and included some browser-fingerprint spoofing to avoid getting blocked. After reading more about it, I realized that approach was sitting in a gray area against most platforms' terms of service, so I rebuilt the whole thing around OpenStreetMap instead. It's public data, built to be queried like this, so none of the spoofing tricks are even needed anymore. I also added a check so the script respects each site's robots.txt before touching it.

## ⚙️ How it works

```
1. Geocode city name  -->  2. Query Overpass API  -->  3. Check site for   -->  4. Save results
   (Nominatim)                for matching             email (robots.txt        to CSV
                              businesses                aware)
```

1. Turns a city name like "Multan, Pakistan" into coordinates using Nominatim
2. Searches OpenStreetMap's Overpass API for businesses matching a category (like "beauty salon") in that area
3. For each business with a website, checks robots.txt first, then looks for a public email through mailto links, page text, or a contact page
4. Saves everything to a CSV, skipping anything already saved from a previous run

## 🛠️ Stack

Python 3.10+, using asyncio and httpx for running requests without blocking on each one, BeautifulSoup + lxml for reading page HTML, urllib.robotparser for checking robots.txt, and dataclasses to keep things structured.

## 🚀 Running it

```bash
git clone https://github.com/ahmadshahmeerkhan/osm-lead-finder.git
cd osm-lead-finder
pip install -r requirements.txt
```

Open lead_scraper.py and edit the niches/cities near the top:

```python
NICHES = ["beauty salon", "spa"]
CITIES = ["Multan, Pakistan", "Lahore, Pakistan"]
```

Then run:

```bash
python lead_scraper.py
```

It saves results to leads.csv in the same folder and prints progress as it goes.

## 📊 Sample output

```csv
niche,city,business_name,phone,website,email,address,osm_url
beauty salon,Multan Pakistan,Glow & Grace Salon,+92 300 1234567,https://glowgrace.example,info@glowgrace.example,Main Boulevard Gulberg,https://www.openstreetmap.org/node/1234567
spa,Multan Pakistan,Serenity Spa,+92 300 7654321,https://serenityspa.example,,Cantt Bazaar,https://www.openstreetmap.org/node/7654321
```

An empty email column just means no public email was found, or the site's robots.txt didn't allow checking it. The script doesn't try to get around that.

## 🔒 A note on the approach

This project only uses OpenStreetMap for finding businesses, which is open data made for exactly this kind of use. When checking a business's own site for an email, it identifies itself honestly in the request headers, checks robots.txt first, and adds a delay between requests instead of hammering a small business's server all at once. There's no fingerprint spoofing or ToS bypass involved because with this approach there's nothing to bypass.

## 🧠 What I got out of this

Mostly, actually understanding asyncio properly, running several requests at once without blocking on each one, and using a semaphore so I'm not overloading anything. The bigger lesson honestly was going back and rebuilding the first version after realizing it wasn't the right approach. That taught me more than if it had just worked the first time.

## 🔭 Possible next steps

- Add some basic tests for the email extraction logic
- Take niches/cities as command line arguments instead of editing the file directly
- Maybe a small Streamlit front end to browse leads instead of a raw CSV

## 📄 License

MIT, see the LICENSE file.

## 📬 Contact

Built by Ahmad Shahmeer Khan. Feel free to open an issue if you have questions.
