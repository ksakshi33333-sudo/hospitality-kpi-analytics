"""Create the SQLite database, load the CSVs, then build the aggregate tables."""
import sqlite3
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "hospitality.db"
RAW = ROOT / "data" / "raw"
LOAD_ORDER = ["hotels", "room_types", "guests", "employees", "bookings", "surveys"]


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")

    print("Creating schema ...")
    con.executescript((ROOT / "sql" / "schema.sql").read_text())

    for t in LOAD_ORDER:
        df = pd.read_csv(RAW / f"{t}.csv")
        df.to_sql(t, con, if_exists="append", index=False, chunksize=50_000)
        print(f"  loaded {t:<11} {len(df):>9,} rows")

    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    print("Foreign-key violations:", len(bad))

    print("Building aggregate tables (SQL) ...")
    t0 = time.time()
    con.executescript((ROOT / "sql" / "aggregates.sql").read_text())
    print(f"  done in {time.time() - t0:.1f}s")

    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for t in tables:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:<28} {n:>9,}")
    con.commit()
    con.close()
    print(f"Database ready: {DB}")


if __name__ == "__main__":
    main()
