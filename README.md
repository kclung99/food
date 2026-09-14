# food

Install dependencies once.

```bash
python3 -m pip install -r requirements.txt
```

Trigger the background worker now.

Manual and scheduled runs publish successful changes to GitHub automatically.

```bash
launchctl kickstart -k gui/$(id -u)/com.kclung.food.process
```

Install the macOS background schedule.

```bash
python3 scripts/install_scheduler.py
```

Stop and remove the macOS background schedule.

```bash
python3 scripts/uninstall_scheduler.py
```

Rebuild the static record data.

```bash
python3 scripts/build_site.py
```

Preview the website locally.

```bash
python3 -m http.server 48173 --directory dist
```

View recent processing events.

```bash
sqlite3 data/food.db "SELECT created_at, level, action, source, message FROM events ORDER BY id DESC LIMIT 30;"
```

View only failures.

```bash
sqlite3 data/food.db "SELECT created_at, source, message FROM events WHERE level='ERROR' ORDER BY id DESC;"
```
