#!/usr/bin/env python3
"""Price monitor with change detection.

Scrapes a listing page, saves a snapshot, and on the next run reports what changed:
new items, removed items, price moves. Writes changes.csv for the client to open.

Usage:
  python monitor.py --snapshot snap.json --changes changes.csv
"""
import argparse
import csv
import json
import os
import sys

import requests
from bs4 import BeautifulSoup

URL = "https://books.toscrape.com/catalogue/page-1.html"
FIELDS = ["change", "title", "old_price", "new_price", "url"]


def fetch() -> dict:
    r = requests.get(URL, timeout=20, headers={"User-Agent": "portfolio-monitor/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = {}
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        price = card.select_one("p.price_color")
        if not link or not price:
            continue
        url = "https://books.toscrape.com/catalogue/" + link["href"].replace("../", "")
        items[url] = {
            "title": link["title"].strip(),
            "price": float("".join(c for c in price.get_text() if c.isdigit() or c == ".")),
        }
    return items


def diff(old: dict, new: dict) -> list:
    rows = []
    for url, item in new.items():
        if url not in old:
            rows.append({"change": "NEW", "title": item["title"], "old_price": "",
                         "new_price": f"{item['price']:.2f}", "url": url})
        elif abs(item["price"] - old[url]["price"]) > 0.001:
            rows.append({"change": "PRICE", "title": item["title"],
                         "old_price": f"{old[url]['price']:.2f}",
                         "new_price": f"{item['price']:.2f}", "url": url})
    for url, item in old.items():
        if url not in new:
            rows.append({"change": "GONE", "title": item["title"],
                         "old_price": f"{item['price']:.2f}", "new_price": "", "url": url})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="snap.json")
    ap.add_argument("--changes", default="changes.csv")
    args = ap.parse_args()

    current = fetch()
    if not current:
        print("scrape returned zero items - refusing to overwrite snapshot", file=sys.stderr)
        return 1

    old = {}
    if os.path.exists(args.snapshot):
        with open(args.snapshot, encoding="utf-8") as f:
            old = json.load(f)

    if not old:
        with open(args.snapshot, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=1)
        with open(args.changes, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
        print(f"baseline created: {len(current)} items tracked, nothing to compare yet")
        return 0

    rows = diff(old, current)
    with open(args.snapshot, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=1)

    with open(args.changes, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["change"]] = counts.get(r["change"], 0) + 1
    print(f"items tracked: {len(current)} | baseline: {'yes' if old else 'no (first run)'}")
    print(f"changes: {counts or 'none'}")
    print(f"wrote {args.changes} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
