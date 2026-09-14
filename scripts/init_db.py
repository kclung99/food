#!/usr/bin/env python3
"""Create the empty local database used by the food worker."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
database = ROOT / 'data' / 'food.db'
with sqlite3.connect(database) as db:
    db.executescript((ROOT / 'data' / 'schema.sql').read_text())
print(f'Initialized {database}')
