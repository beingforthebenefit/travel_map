#!/usr/bin/env python3
"""Seed the database with the Spain & Portugal 2026 sample trip."""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys

DATA_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/data")
DB_PATH = DATA_DIR / "db.sqlite3"


def main():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run the app first to initialize.")
        sys.exit(1)

    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA foreign_keys = ON")

    now = datetime.now(timezone.utc).isoformat()
    trip_id = str(uuid.uuid4())

    db.execute(
        """INSERT INTO trips (id, title, subtitle, created_at, updated_at, style,
           print_width, print_height, dpi)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trip_id, "Spain & Portugal 2026", "March 22 – April 10", now, now,
         "watercolor", 24.0, 18.0, 300),
    )

    stops = [
        ("Madrid", None, 40.4168, -3.7038, "Mar 22–24", 2, True),
        ("Toledo", None, 39.8628, -4.0273, "Mar 24–25", 1, False),
        ("Córdoba", None, 37.8882, -4.7794, "Mar 25–27", 2, False),
        ("Seville", None, 37.3891, -5.9845, "Mar 27–29", 2, True),
        ("Faro", None, 37.0194, -7.9322, "Mar 29–30", 1, False),
        ("Lisbon", None, 38.7223, -9.1393, "Mar 30–Apr 2", 3, True),
        ("Sintra", None, 38.7998, -9.3871, "Apr 2–3", 1, False),
        ("Porto", None, 41.1579, -8.6291, "Apr 3–5", 2, True),
        ("Salamanca", None, 40.9688, -5.6631, "Apr 5–6", 1, False),
        ("Segovia", None, 40.9429, -4.1088, "Apr 6–7", 1, False),
        ("Madrid", "Madrid (return)", 40.4168, -3.7038, "Apr 7–10", 3, True),
    ]

    for i, (city, label, lat, lon, dates, nights, highlight) in enumerate(stops):
        stop_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO stops (id, trip_id, sort_order, city, label, lat, lon,
               dates, nights, highlight, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (stop_id, trip_id, i, city, label, lat, lon, dates, nights,
             int(highlight), now),
        )

    db.commit()
    db.close()
    print(f"Seeded trip '{trip_id}' with {len(stops)} stops.")


if __name__ == "__main__":
    main()
