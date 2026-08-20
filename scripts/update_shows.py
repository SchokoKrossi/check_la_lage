#!/usr/bin/env python3
"""
Scrapes upcoming Check La Lage shows and Improv Playground courses from
rausgegangen.de and updates index.html. Run daily by GitHub Actions.
"""
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Source URLs
SHOWS_URL   = "https://rausgegangen.de/en/events/check-la-lage-improv-show-0/"
COURSES_URL = "https://rausgegangen.de/en/organizations/improv-berlin/"

INDEX_HTML = Path(__file__).parent.parent / "index.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MONTHS   = ["January","February","March","April","May","June",
            "July","August","September","October","November","December"]
WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


# ── helpers ────────────────────────────────────────────────────────────────────

def parse_date(dd_mm_yyyy: str) -> date:
    d, m, y = dd_mm_yyyy.strip().split(".")
    return date(int(y), int(m), int(d))


def fetch_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def event_date_from_page(url: str) -> date | None:
    """Fetch an event page and extract its date from the <title>."""
    try:
        soup = fetch_soup(url)
    except Exception as exc:
        print(f"  fetch error {url}: {exc}")
        return None
    title = soup.find("title")
    if not title:
        return None
    m = re.search(r"on (\d{2}\.\d{2}\.\d{4})", title.text)
    return parse_date(m.group(1)) if m else None


def collect_urls(soup: BeautifulSoup, pattern: str) -> list[str]:
    seen, urls = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http"):
            href = "https://rausgegangen.de" + href
        if re.search(pattern, href) and href not in seen:
            seen.add(href)
            urls.append(href)
    return urls


# ── shows ──────────────────────────────────────────────────────────────────────

def scrape_shows(max_count: int) -> list[dict]:
    today = date.today()
    soup  = fetch_soup(SHOWS_URL)
    urls  = collect_urls(soup, r"check-la-lage-improv-show-\d+/?$")
    print(f"  found {len(urls)} show URL(s)")

    shows = []
    for url in urls:
        show_date = event_date_from_page(url)
        if not show_date or show_date < today:
            print(f"  skip {show_date or url}")
            continue

        # Extract time and price from the page
        try:
            soup2    = fetch_soup(url)
            text     = soup2.get_text(" ", strip=True)
            time_m   = re.search(r"(\d{2}:\d{2})\s*[-–]\s*\d{2}:\d{2}", text)
            price_m  = re.search(r"(\d+)[,.]00\s*€", text)
            show_time  = time_m.group(1)  if time_m  else "20:00"
            show_price = f"{price_m.group(1)} €" if price_m else "5 €"
        except Exception:
            show_time, show_price = "20:00", "5 €"

        shows.append({
            "date":    show_date,
            "day":     show_date.day,
            "month":   MONTHS[show_date.month - 1],
            "weekday": WEEKDAYS[show_date.weekday()],
            "time":    show_time,
            "price":   show_price,
            "url":     url,
        })
        print(f"  + show {show_date}")
        if len(shows) == max_count:
            break

    return sorted(shows, key=lambda s: s["date"])[:max_count]


# ── courses ────────────────────────────────────────────────────────────────────

def scrape_courses(max_count: int) -> list[dict]:
    today = date.today()
    soup  = fetch_soup(COURSES_URL)
    urls  = collect_urls(soup, r"improv-playground-\d+/?$")
    print(f"  found {len(urls)} course URL(s)")

    courses = []
    for url in urls:
        course_date = event_date_from_page(url)
        if not course_date or course_date < today:
            print(f"  skip {course_date or url}")
            continue

        courses.append({
            "date":    course_date,
            "day":     course_date.day,
            "month":   MONTHS[course_date.month - 1],
            "weekday": WEEKDAYS[course_date.weekday()],
            "url":     url,
        })
        print(f"  + course {course_date}")
        if len(courses) == max_count:
            break

    return sorted(courses, key=lambda c: c["date"])[:max_count]


# ── HTML builders ──────────────────────────────────────────────────────────────

def build_shows_html(shows: list[dict]) -> str:
    if not shows:
        return '  <p class="no-show-text">No upcoming shows scheduled — check back soon!</p>'
    cards = []
    for s in shows:
        cards.append(
            f'    <div class="show-card" data-date="{s["date"]}">\n'
            f'      <div class="show-date">{s["day"]}</div>\n'
            f'      <div class="show-month">{s["month"]} · {s["weekday"]}</div>\n'
            f'      <div class="show-venue">Café Engels</div>\n'
            f'      <div class="show-address">Herrfurthstraße 21, 12049 Berlin</div>\n'
            f'      <div class="show-location">{s["price"]} · {s["time"]}</div>\n'
            f'      <a href="{s["url"]}" target="_blank" class="show-ticket-link">Get Tickets →</a>\n'
            f'    </div>'
        )
    inner = "\n\n".join(cards)
    return f'  <div class="shows-grid reveal">\n\n{inner}\n\n  </div>'


def build_courses_html(courses: list[dict]) -> str:
    if not courses:
        return '  <p class="no-show-text">No upcoming sessions scheduled — check back soon!</p>'
    cards = []
    for c in courses:
        cards.append(
            f'    <div class="show-card reveal" data-date="{c["date"]}">\n'
            f'      <span class="show-tag">Improv Playground · Open Level</span>\n'
            f'      <div class="show-date">{c["day"]}</div>\n'
            f'      <div class="show-month">{c["month"]} · {c["weekday"]}</div>\n'
            f'      <div class="show-venue">Hotel Continental</div>\n'
            f'      <div class="show-address">ArtSpaceInExile · Berlin</div>\n'
            f'      <div class="show-location">20 € per session · 19:00</div>\n'
            f'      <a href="{c["url"]}" target="_blank" class="show-ticket-link">Book a Spot →</a>\n'
            f'    </div>'
        )
    inner = "\n\n".join(cards)
    return f'  <div class="shows-grid">\n\n{inner}\n\n  </div>'


# ── HTML updater ───────────────────────────────────────────────────────────────

def update_section(content: str, start_marker: str, end_marker: str, html_block: str) -> str:
    if start_marker not in content or end_marker not in content:
        raise ValueError(f"Markers not found: {start_marker!r}")
    start = content.index(start_marker) + len(start_marker)
    end   = content.index(end_marker)
    return content[:start] + "\n" + html_block + "\n  " + content[end:]


# ── main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Scraping shows ===")
    try:
        shows = scrape_shows(max_count=2)
    except Exception as exc:
        print(f"ERROR scraping shows: {exc}")
        sys.exit(1)

    print(f"\n=== Scraping courses ===")
    try:
        courses = scrape_courses(max_count=4)
    except Exception as exc:
        print(f"ERROR scraping courses: {exc}")
        sys.exit(1)

    print(f"\n=== Updating index.html ===")
    content = INDEX_HTML.read_text(encoding="utf-8")
    try:
        content = update_section(content, "<!-- SHOWS:BEGIN -->",   "<!-- SHOWS:END -->",   build_shows_html(shows))
        content = update_section(content, "<!-- COURSES:BEGIN -->", "<!-- COURSES:END -->", build_courses_html(courses))
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    original = INDEX_HTML.read_text(encoding="utf-8")
    if content == original:
        print("No changes.")
    else:
        INDEX_HTML.write_text(content, encoding="utf-8")
        print(f"Updated — {len(shows)} show(s), {len(courses)} course(s).")
