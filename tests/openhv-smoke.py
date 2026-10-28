#!/usr/bin/env python3
"""Installed OpenHV with private Shield Mesa; CPU fallback, no GPU claim."""
import json,os,pathlib,subprocess,tempfile,time
out=pathlib.Path('/out')
with tempfile.TemporaryDirectory() as home:
    env=dict(os.environ,HOME=home,ALSOFT_DRIVERS='null',XDG_RUNTIME_DIR=home)
    with (out/'openhv-smoke.log').open('w') as log:
        game=subprocess.Popen(['/usr/bin/enclave-openhv','Graphics.WindowMode=Windowed'],env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+int(os.environ.get("ENCLAVE_GAME_START_TIMEOUT","90"))
            while time.monotonic()<deadline:
                assert game.poll() is None, (out/'openhv-smoke.log').read_text()
                windows=subprocess.run(['xdotool','search','--onlyvisible','--pid',str(game.pid)],capture_output=True,text=True)
                if windows.returncode==0:
                    time.sleep(10)
                    assert game.poll() is None, (out/'openhv-smoke.log').read_text()
                    (out/'results.json').write_text(json.dumps({'visibleWindow':True,'survivedSeconds':10,'gpuExecution':False,'audioQualification':False})+'\n')
                    break
                time.sleep(1)
            else: raise AssertionError('No OpenHV window: '+(out/'openhv-smoke.log').read_text())
        finally:
            game.terminate()
            try:game.wait(timeout=5)
            except subprocess.TimeoutExpired:game.kill();game.wait()
            import shutil
            support=pathlib.Path(home)/'.local/share/enclave-openhv'
            if support.exists():shutil.copytree(support,out/'support',dirs_exist_ok=True)
