#!/usr/bin/env python3
"""Stop and remove the food capture LaunchAgent."""
import os, subprocess
from pathlib import Path

label = 'com.kclung.food.process'
plist = Path.home() / 'Library' / 'LaunchAgents' / f'{label}.plist'
subprocess.run(['launchctl', 'bootout', f'gui/{os.getuid()}', str(plist)], check=False)
if plist.exists(): plist.unlink()
check = subprocess.run(['launchctl', 'print', f'gui/{os.getuid()}/{label}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'Removed {label}' if check.returncode != 0 else f'Warning: {label} is still loaded')
