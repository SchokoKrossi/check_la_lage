#!/usr/bin/env python3
"""
Builds the upcoming-shows parts of index.html from shows.json.

Edit shows.json (date, time, price, ticket link), push, and GitHub Actions
runs this script. It also runs daily so past shows drop off the page.

Updates three marked regions in index.html:
  HERO-NEXT  - the "next show" box in the hero
  SHOWS      - the show cards in the Shows section
  EVENTS-LD  - schema.org Event data so Google can list the shows
"""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT       = Path(__file__).parent.parent
SHOWS_JSON = ROOT / "shows.json"
INDEX_HTML = ROOT / "index.html"
SITE_URL   = "https://schokokrossi.github.io/check_la_lage/"
MAX_SHOWS  = 2

MONTHS   = ["January","February","March","April","May","June",
            "July","August","September","October","November","December"]
WEEKDAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

DEFAULTS = {
    "time":    "20:00",
    "price":   "5 €",
    "venue":   "Café Engels",
    "address": "Herrfurthstraße 21, 12049 Berlin",
}


# ── data ───────────────────────────────────────────────────────────────────────

def load_shows() -> list[dict]:
    data  = json.loads(SHOWS_JSON.read_text(encoding="utf-8"))
    today = date.today()
    shows = []
    for raw in data.get("shows", []):
        s = {**DEFAULTS, **raw}
        d = date.fromisoformat(s["date"])
        if d < today:
            continue
        s.update(
            d=d,
            day=d.day,
            month=MONTHS[d.month - 1],
            weekday=WEEKDAYS[d.weekday()],
        )
        shows.append(s)
    return sorted(shows, key=lambda s: s["d"])[:MAX_SHOWS]


def berlin_offset(d: date) -> str:
    """UTC offset for Berlin: CEST from last Sunday of March to last Sunday of October."""
    def last_sunday(month: int) -> date:
        last = date(d.year, month, 31)
        return date.fromordinal(last.toordinal() - (last.weekday() + 1) % 7)
    return "+02:00" if last_sunday(3) <= d < last_sunday(10) else "+01:00"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


# ── HTML builders ──────────────────────────────────────────────────────────────

def build_shows_html(shows: list[dict]) -> str:
    if not shows:
        return '  <p class="no-show-text">No upcoming shows scheduled — check back soon!</p>'
    cards = []
    for s in shows:
        cards.append(
            f'    <div class="show-card" data-date="{s["d"]}">\n'
            f'      <div class="show-date">{s["day"]}</div>\n'
            f'      <div class="show-month">{s["month"]} · {s["weekday"]}</div>\n'
            f'      <div class="show-venue">{esc(s["venue"])}</div>\n'
            f'      <div class="show-address">{esc(s["address"])}</div>\n'
            f'      <div class="show-location">{esc(s["price"])} · {esc(s["time"])}</div>\n'
            f'      <a href="{esc(s["ticket_url"])}" target="_blank" rel="noopener" class="show-ticket-link">Get Tickets →</a>\n'
            f'    </div>'
        )
    inner = "\n\n".join(cards)
    return f'  <div class="shows-grid reveal">\n\n{inner}\n\n  </div>'


def build_hero_next_html(shows: list[dict]) -> str:
    if not shows:
        return (
            '      <div class="hero-cta">\n'
            '        <a href="#newsletter" class="btn btn-primary">Get notified about the next show</a>\n'
            '      </div>'
        )
    s = shows[0]
    return (
        f'      <div class="next-show" data-date="{s["d"]}">\n'
        f'        <div class="next-show-label">Next show</div>\n'
        f'        <div class="next-show-date">{s["weekday"]}, {s["day"]} {s["month"]} · {esc(s["time"])}</div>\n'
        f'        <div class="next-show-venue">{esc(s["venue"])} · {esc(s["address"])}</div>\n'
        f'        <div class="next-show-price">{esc(s["price"])}</div>\n'
        f'      </div>\n'
        f'      <div class="hero-cta">\n'
        f'        <a href="{esc(s["ticket_url"])}" target="_blank" rel="noopener" class="btn btn-primary">Get Tickets</a>\n'
        f'        <a href="#shows" class="btn btn-ghost">All dates</a>\n'
        f'      </div>'
    )


def build_events_ld(shows: list[dict]) -> str:
    events = []
    for s in shows:
        street, _, rest = s["address"].partition(",")
        postal, _, city = rest.strip().partition(" ")
        price_digits = "".join(ch for ch in s["price"].split("€")[0] if ch.isdigit() or ch in ".,").replace(",", ".")
        events.append({
            "@context": "https://schema.org",
            "@type": "TheaterEvent",
            "name": "Check la Lage – Improv Show",
            "description": "Unscripted improv theatre: every scene is made up on the spot from audience suggestions.",
            "startDate": f'{s["d"]}T{s["time"]}:00{berlin_offset(s["d"])}',
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "image": [SITE_URL + "images/group-web.png"],
            "location": {
                "@type": "Place",
                "name": s["venue"],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": street.strip(),
                    "postalCode": postal,
                    "addressLocality": city or "Berlin",
                    "addressCountry": "DE",
                },
            },
            "offers": {
                "@type": "Offer",
                "url": s["ticket_url"],
                "price": price_digits or "0",
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock",
            },
            "organizer": {"@type": "PerformingGroup", "name": "Check la Lage", "url": SITE_URL},
        })
    payload = json.dumps(events, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{payload}\n</script>'


# ── HTML updater ───────────────────────────────────────────────────────────────

def update_section(content: str, name: str, block: str, indent: str = "  ") -> str:
    start_marker, end_marker = f"<!-- {name}:BEGIN -->", f"<!-- {name}:END -->"
    if start_marker not in content or end_marker not in content:
        raise ValueError(f"Markers not found: {start_marker!r}")
    start = content.index(start_marker) + len(start_marker)
    end   = content.index(end_marker)
    return content[:start] + "\n" + block + "\n" + indent + content[end:]


# ── main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        shows = load_shows()
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR reading {SHOWS_JSON.name}: {exc}")
        sys.exit(1)
    print(f"{len(shows)} upcoming show(s)")

    original = INDEX_HTML.read_text(encoding="utf-8")
    try:
        content = update_section(original, "HERO-NEXT", build_hero_next_html(shows), indent="      ")
        content = update_section(content, "SHOWS", build_shows_html(shows))
        content = update_section(content, "EVENTS-LD", build_events_ld(shows), indent="")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    if content == original:
        print("No changes.")
    else:
        INDEX_HTML.write_text(content, encoding="utf-8")
        print("index.html updated.")
