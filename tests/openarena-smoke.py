#!/usr/bin/env python3
import os, pathlib, subprocess, tempfile, time
with tempfile.TemporaryDirectory() as home:
    env = dict(os.environ, HOME=home, LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', LP_NUM_THREADS='1', SDL_AUDIODRIVER='dummy', SHIELD_INPUT_STATE=home+'/input-state')
    log_path = pathlib.Path('/out/openarena-smoke.log')
    with log_path.open('w') as log:
        game = subprocess.Popen(['/usr/lib/enclave-os/openarena/ioquake3', '+set', 'com_basegame', 'baseoa', '+set', 'fs_basepath', '/usr/lib/enclave-os/openarena', '+set', 'com_homepath', '.openarena', '+set', 'vm_ui', '0', '+set', 'vm_cgame', '0', '+set', 'vm_game', '0', '+set', 'r_allowSoftwareGL', '1', '+set', 'r_fullscreen', '0', '+set', 's_initsound', '0', '+set', 'in_absoluteMenu', '1'], stdout=log, stderr=subprocess.STDOUT, env=env)
        try:
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                assert game.poll() is None, log_path.read_text()
                windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--pid', str(game.pid)], capture_output=True, text=True)
                if windows.returncode == 0 and pathlib.Path(home+'/input-state').exists():
                    time.sleep(5)
                    assert game.poll() is None, log_path.read_text()
                    print('PASS: patched musl OpenArena produced a visible window and input-mode state (CPU rendering only).')
                    break
                time.sleep(.5)
            else:
                raise AssertionError('No game window/input state: ' + log_path.read_text())
        finally:
            game.terminate()
            try: game.wait(timeout=10)
            except subprocess.TimeoutExpired:
                game.kill(); game.wait()
