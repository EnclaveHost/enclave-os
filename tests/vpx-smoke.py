#!/usr/bin/env python3
"""Installed VPX table startup through private Mesa, with isolated null audio."""
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time
from PIL import Image

OUT = Path('/out')
ENGINE = Path('/usr/lib/enclave-os/vpinball')


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


with tempfile.TemporaryDirectory() as directory:
    home = Path(directory)
    env = dict(os.environ, HOME=directory, XDG_RUNTIME_DIR=directory,
               PULSE_SERVER=f'unix:{directory}/audio.sock', SDL_AUDIODRIVER='pulseaudio')
    with (OUT/'pulse.log').open('w') as log:
        pulse = subprocess.Popen(['pulseaudio', '--daemonize=no', '--exit-idle-time=-1', '-n',
            '--load=module-native-protocol-unix socket='+directory+'/audio.sock auth-anonymous=1',
            '--load=module-null-sink sink_name=test rate=48000'], env=env, stdout=log, stderr=log)
    with (OUT/'fluxbox.log').open('w') as log:
        window_manager = subprocess.Popen(['fluxbox'], env=env, stdout=log, stderr=log)
    try:
        deadline = time.monotonic()+10
        while not (home/'audio.sock').is_socket():
            assert pulse.poll() is None, (OUT/'pulse.log').read_text()
            assert time.monotonic() < deadline
            time.sleep(.1)
        deadline = time.monotonic()+15
        while True:
            assert window_manager.poll() is None, (OUT/'fluxbox.log').read_text()
            property = subprocess.run(['xprop','-root','_NET_SUPPORTING_WM_CHECK'],
                env=env,capture_output=True,text=True,timeout=5)
            if 'window id #' in property.stdout:
                break
            assert time.monotonic() < deadline, property.stdout
            time.sleep(.1)
        results = []
        for name, table in [('current', ENGINE/'tables/default-table.vpx'),
                            ('retained', Path('/usr/share/enclave-os/vpinball/exampleTable.vpx'))]:
            preferences = home/name
            preferences.mkdir()
            tables = preferences/'tables'
            tables.mkdir()
            writable_table = tables/table.name
            shutil.copyfile(table,writable_table)
            ini = preferences/'VPinballX.ini'
            ini.write_text('[Player]\nFullScreen=0\nWidth=960\nHeight=600\nMaxFramerate=30\nSyncMode=0\n')
            with (OUT/f'{name}.log').open('w') as log:
                command = ([str(ENGINE/'VPinballX_GL'), '-LessCPUthreads',
                    '-PrefPath', str(preferences), '-Ini', str(ini), '-Play', str(writable_table)]
                    if name == 'current' else ['/usr/bin/enclave-vpinball'])
                game = subprocess.Popen(command,
                    cwd=ENGINE, env=env, stdout=log, stderr=log)
            try:
                deadline = time.monotonic()+120
                while time.monotonic() < deadline:
                    assert game.poll() is None, (OUT/f'{name}.log').read_text()
                    windows = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', 'Visual Pinball'], capture_output=True, text=True, env=env)
                    if windows.returncode == 0:
                        window = windows.stdout.splitlines()[0]
                        subprocess.run(['xdotool', 'windowactivate', '--sync', window], env=env, check=True, timeout=5)
                        time.sleep(15)
                        assert game.poll() is None, (OUT/f'{name}.log').read_text()
                        assert pulse.poll() is None, (OUT/'pulse.log').read_text()
                        capture = subprocess.check_output(['/tmp/capture'], env=env, timeout=10)
                        assert capture[:4] == b'RGB1'
                        width, height, _, _ = struct.unpack('>4I', capture[4:20])
                        assert (width, height) == (960, 600)
                        Image.frombytes('RGB', (width,height), capture[20:]).save(OUT/f'{name}.png')
                        results.append({'table':name,'visibleWindow':True,'survivedSeconds':15})
                        break
                    time.sleep(1)
                else:
                    tree = subprocess.run(['xwininfo', '-root', '-tree'], env=env,
                        capture_output=True, text=True, timeout=10)
                    (OUT/f'{name}-windows.log').write_text(tree.stdout+tree.stderr)
                    capture = subprocess.check_output(['/tmp/capture'], env=env, timeout=10)
                    assert capture[:4] == b'RGB1'
                    width, height, _, _ = struct.unpack('>4I', capture[4:20])
                    Image.frombytes('RGB', (width,height), capture[20:]).save(OUT/f'{name}-failure.png')
                    raise AssertionError('No VPX player window: '+(OUT/f'{name}.log').read_text())
            finally:
                stop(game)
                if name == 'retained':
                    seeded = home/'.local/share/enclave-vpinball/tables/exampleTable.vpx'
                    assert seeded.read_bytes() == table.read_bytes()
                    assert (home/'.config/enclave-vpinball/VPinballX.ini').is_file()
                shutil.copytree(preferences, OUT/f'{name}-preferences', dirs_exist_ok=True)
        (OUT/'results.json').write_text(json.dumps({'tables':results,'gpuExecution':False,
            'streamedInputQualification':False,'audioQualification':False},indent=2)+'\n')
    finally:
        stop(window_manager)
        stop(pulse)
