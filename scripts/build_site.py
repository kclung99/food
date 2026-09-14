#!/usr/bin/env python3
"""Export SQLite records as the tiny data file consumed by the static page."""
import json, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with sqlite3.connect(ROOT / 'data' / 'food.db') as db:
    db.row_factory = sqlite3.Row
    records = [dict(row) for row in db.execute('SELECT id,source_timestamp,model FROM records ORDER BY source_timestamp DESC, created_at DESC')]
(ROOT / 'dist' / 'records.js').write_text('window.FOOD_RECORDS = ' + json.dumps(records) + ';\n')
print(f'Built {len(records)} records into dist/records.js')
