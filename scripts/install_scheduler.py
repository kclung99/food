#!/usr/bin/env python3
"""Install the local macOS schedule: process captures at 09:00, 15:00, and 21:00."""
import os, plistlib, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
label = 'com.kclung.food.process'
plist_path = Path.home() / 'Library' / 'LaunchAgents' / f'{label}.plist'
plist_path.parent.mkdir(parents=True, exist_ok=True)
python = ROOT / '.venv' / 'bin' / 'python3'
if not python.exists(): python = Path('/usr/bin/python3')
plist = {
    'Label': label,
    'ProgramArguments': [str(python), str(ROOT / 'scripts' / 'process_captures.py')],
    'WorkingDirectory': str(ROOT),
    'EnvironmentVariables': {
        'PATH': '/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
    },
    'StartCalendarInterval': [{'Hour': hour, 'Minute': 0} for hour in (9, 15, 21)],
    'StandardOutPath': str(ROOT / 'runs' / 'scheduler.log'),
    'StandardErrorPath': str(ROOT / 'runs' / 'scheduler-error.log'),
}
plist_path.write_bytes(plistlib.dumps(plist))
uid = os.getuid()
subprocess.run(['launchctl', 'bootout', f'gui/{uid}', str(plist_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(['launchctl', 'bootstrap', f'gui/{uid}', str(plist_path)], check=True)
print(f'Installed {label}: 09:00, 15:00, 21:00')
