#!/usr/bin/python3 -I
import os
from pathlib import Path
import shutil
import tempfile

cache = Path.home() / '.cache'
cache.mkdir(exist_ok=True, mode=0o700)
games = [('FreeDoom', 'enclave-doom'), ('OpenArena', 'enclave-openarena'), ('LibreQuake', 'enclave-librequake'), ('Visual Pinball X', 'enclave-vpinball'), ('OpenHV', 'enclave-openhv')]
with tempfile.NamedTemporaryFile(mode='w', dir=cache, prefix='.enclave-games-', delete=False) as out:
    for label, command in games:
        if shutil.which(command):
            out.write(f'  [exec] ({label}) {{{command}}}\n')
os.replace(out.name, cache / 'enclave-games.menu')
