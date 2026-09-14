#!/usr/bin/env python3
"""Process today's photos from one flat capture directory, once each."""
import argparse, os, sqlite3, subprocess, sys
from datetime import date, datetime
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.heic'}

def load_env():
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"\''))

def log(db, level, action, message, source=None):
    db.execute('INSERT INTO events(level,action,source,message) VALUES (?,?,?,?)', (level, action, source, message))
    db.commit()

def source_time(image):
    exif = Image.open(image).getexif()
    value = exif.get(36867) or exif.get(306)
    if value:
        return value.replace(':', '-', 2).replace(' ', 'T')
    return datetime.fromtimestamp(image.stat().st_mtime).isoformat(timespec='seconds')

def slug(image, timestamp):
    return f'{image.stem.lower()}-{timestamp[:10]}'

def main():
    load_env()
    parser = argparse.ArgumentParser()
    parser.add_argument('--captures', type=Path, default=Path(os.environ['CAPTURE_DIR']))
    args = parser.parse_args()
    if not args.captures.exists(): raise SystemExit(f'Capture directory does not exist: {args.captures}')
    database = ROOT / 'data' / 'food.db'
    if not database.exists():
        subprocess.run([sys.executable, str(ROOT / 'scripts' / 'init_db.py')], check=True)
    today = date.today().isoformat()
    images = sorted(x for x in args.captures.iterdir() if x.is_file() and x.suffix.lower() in EXTENSIONS)
    with sqlite3.connect(database) as db:
        log(db, 'INFO', 'scan_started', f'Scanning {args.captures} for {today}')
        processed = skipped = 0
        for image in images:
            source = str(image.resolve())
            timestamp = source_time(image)
            if timestamp[:10] != today:
                log(db, 'INFO', 'skipped', f'Photo date is {timestamp[:10]}', source)
                skipped += 1
                continue
            existing = db.execute('SELECT id,status FROM records WHERE source=?', (source,)).fetchone()
            if existing and existing[1] in {'succeeded', 'processing'}:
                log(db, 'INFO', 'skipped', f'Already {existing[1]}', source)
                skipped += 1
                continue
            name = slug(image, timestamp)
            output = ROOT / 'runs' / name
            target = ROOT / 'dist' / 'assets' / f'{name}.glb'
            if existing:
                db.execute("UPDATE records SET status='processing', error=NULL WHERE source=?", (source,)); db.commit()
            else:
                db.execute('INSERT INTO records(id,date,source_timestamp,original_model,model,source,status) VALUES (?,?,?,?,?,?,?)', (name,timestamp[:10],timestamp,f'runs/{name}/model.glb',f'assets/{target.name}',source,'processing')); db.commit()
            try:
                log(db, 'INFO', 'meshy_started', '1 image', source)
                subprocess.run([sys.executable, str(ROOT/'scripts/run_meshy.py'), str(image), '--output', str(output)], check=True)
                subprocess.run([str(ROOT/'scripts/compress_glb.sh'), str(output/'model.glb'), str(target)], check=True)
                db.execute("UPDATE records SET status='succeeded', error=NULL WHERE source=?", (source,)); db.commit()
                log(db, 'INFO', 'completed', f'Created {name}', source)
                processed += 1
            except Exception as error:
                db.execute("UPDATE records SET status='failed', error=? WHERE source=?", (f'{type(error).__name__}: {error}', source)); db.commit()
                log(db, 'ERROR', 'failed', f'{type(error).__name__}: {error}', source)
                print(f'Failed {image.name}: {error}', file=sys.stderr)
        log(db, 'INFO', 'scan_completed', f'Found {len(images)} photo(s); processed {processed}; skipped {skipped}')
    subprocess.run([sys.executable, str(ROOT/'scripts/build_site.py')], check=True)

if __name__ == '__main__': main()
