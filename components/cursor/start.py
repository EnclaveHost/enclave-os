#!/usr/bin/python3 -I
"""Launch the optional cursor supervisor without joining Fluxbox's process group."""
from pathlib import Path
import os, subprocess
root = Path(__file__).resolve().parent
cache = Path.home() / '.cache'
cache.mkdir(exist_ok=True)
with (cache / 'shield-cursor-supervisor.log').open('a') as log:
    subprocess.Popen(['/usr/bin/python3', '-I', str(root / 'supervise.py')],
                     env=dict(os.environ),
                     stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                     start_new_session=True)
