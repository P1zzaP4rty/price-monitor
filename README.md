# Price monitor demo — scrape, snapshot, report what changed

Third demo: not "get me the data once", but "watch it and tell me when it moves". That's
the request most scraping jobs turn into on week two.

## What it does

Run it on a schedule. First run stores a baseline. Every later run compares live data
against the stored snapshot and writes `changes.csv` with three kinds of row:

- `NEW` — item appeared that wasn't in the baseline
- `PRICE` — same item, different price
- `GONE` — item disappeared from the page

## Verified runs (`run.log`)

```
=== run 1: baseline ===
baseline created: 20 items tracked, nothing to compare yet

=== run 2: nothing changed ===
items tracked: 20 | baseline: yes
changes: none

=== run 3: simulated price move (+3.00 on one item) ===
  editing A Light in the Attic 51.77 -> 54.77
items tracked: 20 | baseline: yes
changes: {'PRICE': 1}
```

`changes.csv` from run 3:

```
change,title,old_price,new_price,url
PRICE,A Light in the Attic,54.77,51.77,https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
```

Run 3's delta is **simulated on purpose**: the stored snapshot was edited to hold 54.77 so
the next real fetch would differ. The scrape itself is real; only the "old" value was
faked to exercise the PRICE branch without waiting for the site to change.

## Tests

Diff logic is covered offline, no network needed:

```
python -m unittest -v
Ran 6 tests in 0.000s
OK
```

Cases: first run, price move, no change, removal, mixed run, float-noise suppression
(a 0.0004 difference is not a price change).

## Safety rails

- refuses to overwrite the snapshot when a scrape returns zero items — a blocked or
  broken page must not wipe the baseline and report everything as `GONE` next run
- exit 1 on empty scrape so a scheduler surfaces the failure
- snapshot and output are plain JSON/CSV, so a client can inspect them without the code

## Scheduling

Cron on a server, or Windows Task Scheduler:

```
0 */6 * * *  cd /srv/monitor && python monitor.py --snapshot snap.json --changes changes.csv
```

Wire `changes.csv` to email/Slack with one more line — that's the part that makes it a
product rather than a script, and it's quoted separately.
