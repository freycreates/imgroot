#!/usr/bin/env python3
"""Update the next BOPS event from The Other Side's public agenda."""

from datetime import date
from html import unescape
from pathlib import Path
import json
import re
import urllib.request

SOURCE = "https://the-other-side.nl/"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "bops-event.json"
MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "MEI": 5,
    "JUN": 6, "JUL": 7, "AUG": 8, "SEP": 9, "SEPT": 9,
    "OCT": 10, "OKT": 10, "NOV": 11, "DEC": 12,
}


def text(fragment):
    fragment = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", fragment,
                      flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


request = urllib.request.Request(SOURCE, headers={"User-Agent": "EvertGrootWebsite/1.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    page = response.read().decode("utf-8", errors="replace")

today = date.today()
events = []
for section in re.findall(r"<section\b.*?</section>", page, flags=re.I | re.S):
    headings = [text(item) for item in re.findall(r"<h[12]\b.*?</h[12]>", section,
                                                   flags=re.I | re.S)]
    titles = [item for item in headings if re.search(r"\bBOPS\b", item, flags=re.I)]
    if not titles:
        continue

    day = next((int(item) for item in headings if re.fullmatch(r"\d{1,2}", item)), None)
    month_name = next((item.upper() for item in headings if item.upper() in MONTHS), None)
    if not day or not month_name:
        continue

    try:
        event_date = date(today.year, MONTHS[month_name], day)
    except ValueError:
        continue
    if event_date < today:
        continue

    hrefs = [unescape(url) for url in re.findall(r"href=[\"']([^\"']+)[\"']", section,
                                                 flags=re.I)]
    ticket_url = next((url for url in hrefs if url.startswith("http")), None)
    title = re.sub(r"\s+", " ", titles[0]).strip()
    events.append((event_date, title, ticket_url))

# The page contains separate desktop/mobile copies, so deduplicate by date and title.
unique = {(event_date, title): ticket for event_date, title, ticket in events}
ordered = sorted((event_date, title, ticket) for (event_date, title), ticket in unique.items())

if ordered:
    event_date, title, ticket_url = ordered[0]
    payload = {
        "date": event_date.isoformat(),
        "displayDate": f"{event_date.day} {event_date.strftime('%B')}",
        "title": title,
        "ticketUrl": ticket_url,
        "source": SOURCE,
        "checkedAt": today.isoformat(),
    }
else:
    payload = {
        "date": None,
        "displayDate": None,
        "title": None,
        "ticketUrl": None,
        "source": SOURCE,
        "checkedAt": today.isoformat(),
    }

OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Updated {OUTPUT}: {payload['title'] or 'no upcoming BOPS event'}")
