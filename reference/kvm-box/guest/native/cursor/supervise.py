#!/usr/bin/env python3
"""One cursor owner per guest display, with bounded crash/hang recovery."""
import fcntl, json, os, signal, subprocess, time
from pathlib import Path
root = Path(__file__).resolve().parent
cache = Path.home() / '.cache'
cache.mkdir(exist_ok=True)
lock = (cache / 'shield-cursor-supervisor.lock').open('w')
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit(0)
status = cache / 'shield-cursor.json'
running = True
child = None

def stop(*_):
    global running
    running = False

signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
env = dict(os.environ, DISPLAY=':0', XAUTHORITY='/run/user/1000/Xauthority')
failures = 0
while running:
    started = time.monotonic()
    logpath = cache / 'shield-cursor.log'
    if logpath.exists() and logpath.stat().st_size > 65536:
        logpath.replace(cache / 'shield-cursor.previous.log')
    with logpath.open('a') as log:
        child = subprocess.Popen([str(root / 'cursor-owner'), str(status)], env=env,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        while running and child.poll() is None:
            time.sleep(.2)
            # Handles an X connection that stalls without returning an error.
            if time.monotonic() - started > 3:
                try:
                    stale = time.time() - status.stat().st_mtime > 2
                except FileNotFoundError:
                    stale = True
                if stale:
                    print('Restarting cursor owner after stale heartbeat', file=log, flush=True)
                    break
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    if child.returncode == 4:  # Another singleton renderer is already present.
        break
    failures = failures + 1 if time.monotonic() - started < 3 else 0
    delay = min(5, .1 * (2 ** min(failures, 6)))
    until = time.monotonic() + delay
    while running and time.monotonic() < until:
        time.sleep(.05)
