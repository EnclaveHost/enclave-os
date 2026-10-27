#!/usr/bin/env python3
"""Authenticated X, visible cursor, singleton and crash/hang recovery; real APKs."""
import json, os, pathlib, secrets, signal, subprocess, tempfile, time

def eventually(check,timeout=15):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:
            value=check()
            if value:return value
        except (FileNotFoundError,json.JSONDecodeError,subprocess.CalledProcessError):pass
        time.sleep(.1)
    raise AssertionError('condition did not recover before deadline')

with tempfile.TemporaryDirectory() as td:
    home=pathlib.Path(td);auth=home/'Xauthority';auth.touch();auth.chmod(0o600)
    env=dict(os.environ, HOME=td,DISPLAY=':91',XAUTHORITY=str(auth))
    subprocess.run(['xauth','-f',str(auth),'add',':91','.',secrets.token_hex(16)],check=True)
    x=subprocess.Popen(['Xvfb',':91','-screen','0','960x600x24','-nolisten','tcp','-auth',str(auth)],env=env)
    supervisor=None
    try:
        eventually(lambda: pathlib.Path('/tmp/.X11-unix/X91').exists())
        bad=dict(env,XAUTHORITY=str(home/'missing'))
        rejected=subprocess.run(['/usr/libexec/enclave-os/cursor/cursor-owner',str(home/'denied.json')],env=bad,timeout=5)
        assert rejected.returncode!=0,'unauthenticated X connection was accepted'
        supervisor=subprocess.Popen(['/usr/bin/python3','-I','/usr/libexec/enclave-os/cursor/supervise.py'],env=env)
        status=home/'.cache/shield-cursor.json'
        def read():return json.loads(status.read_text())
        initial=eventually(lambda: read() if read()['frames']>=3 else None)
        subprocess.run(['/tmp/cursor-image'],env=env,check=True)
        duplicate=subprocess.run(['/usr/libexec/enclave-os/cursor/cursor-owner',str(status)],env=env,timeout=5)
        assert duplicate.returncode==4
        os.kill(initial['pid'],signal.SIGKILL)
        second=eventually(lambda: read() if read()['pid']!=initial['pid'] and read()['frames']>=3 else None)
        os.kill(second['pid'],signal.SIGSTOP)
        third=eventually(lambda: read() if read()['pid']!=second['pid'] and read()['frames']>=3 else None)
        assert third['xErrors']==0
        subprocess.run(['/tmp/cursor-image'],env=env,check=True)
        # Exercise the custom musl fbDOOM executable with real X and its bundled WAD.
        with (home/'doom.log').open('w') as log:
            game=subprocess.Popen(['/usr/bin/enclave-xdoom','-iwad','/usr/share/games/doom/freedoom1.wad','-nosound','-nomusic','-timedemo','demo1'],cwd=td,env=env,stdout=log,stderr=log)
            try:
                time.sleep(3)
                assert game.poll() in (None,0), (home/'doom.log').read_text()
            finally:
                if game.poll() is None:game.terminate();game.wait(timeout=10)
        subprocess.run(['/tmp/cursor-image'],env=env,check=True)
        print('PASS: X authorization, XFixes cursor, singleton, crash/hang recovery, FreeDoom startup')
    finally:
        if supervisor is not None:
            supervisor.terminate();supervisor.wait(timeout=10)
        x.terminate();x.wait(timeout=10)
