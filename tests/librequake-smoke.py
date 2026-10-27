#!/usr/bin/env python3
import os, pathlib, subprocess, tempfile, time
with tempfile.TemporaryDirectory() as home:
    env = dict(os.environ, HOME=home, LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', LP_NUM_THREADS='1', SDL_AUDIODRIVER='dummy')
    log_path = pathlib.Path('/out/librequake-smoke.log')
    with log_path.open('w') as log:
        game = subprocess.Popen(['/usr/libexec/enclave-os/quakespasm', '-basedir', '/usr/share/enclave-os/librequake', '-window', '-width', '960', '-height', '600', '-nosound', '+map', 'start'], stdout=log, stderr=subprocess.STDOUT, env=env)
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                assert game.poll() is None, log_path.read_text()
                windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--pid', str(game.pid)], capture_output=True, text=True)
                if windows.returncode == 0:
                    time.sleep(5)
                    assert game.poll() is None, log_path.read_text()
                    print('PASS: custom musl QuakeSpasm created a visible window and remained alive with LibreQuake content (CPU rendering only).')
                    break
                time.sleep(.5)
            else:
                raise AssertionError('No game window: ' + log_path.read_text())
        finally:
            game.terminate()
            try: game.wait(timeout=10)
            except subprocess.TimeoutExpired:
                game.kill(); game.wait()
