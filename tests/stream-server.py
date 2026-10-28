#!/usr/bin/env python3
"""Private synthetic desktop for the real Sunshine/Moonlight wire test."""
import json,os,pathlib,signal,subprocess,time
fixture=pathlib.Path('/fixture');out=pathlib.Path('/out')
home=fixture/'server-home';home.mkdir(exist_ok=True)
runtime=home/'runtime';runtime.mkdir(mode=0o700,exist_ok=True)
env={**os.environ,'HOME':str(home),'XDG_RUNTIME_DIR':str(runtime)}
config=home/'sunshine.conf'
config.write_text('''sunshine_name = Enclave CI
capture = x11
encoder = software
sw_preset = ultrafast
sw_tune = zerolatency
hevc_mode = 1
av1_mode = 1
bind_address = 127.0.0.1
address_family = ipv4
upnp = disabled
lan_encryption_mode = 2
wan_encryption_mode = 2
origin_web_ui_allowed = pc
stream_audio = enabled
file_apps = /fixture/apps.json
credentials_file = /fixture/server-home/state.json
pkey = /fixture/key.pem
cert = /fixture/cert.pem
''')
(fixture/'apps.json').write_text(json.dumps({'env':{},'apps':[{'name':'Enclave CI Desktop'}]}))
password=(fixture/'password').read_text()
children=[]
try:
    with open('/tmp/credentials.log','w') as log:
        subprocess.run(['/usr/bin/enclave-sunshine',str(config),'--creds','ci',password],check=True,env=env,stdout=log,stderr=log)
    pulse_log=(out/'pulse-server.log').open('w')
    children.append(subprocess.Popen(['pulseaudio','--daemonize=no','--exit-idle-time=-1'],env=env,stdout=pulse_log,stderr=pulse_log))
    for _ in range(100):
        if (runtime/'pulse/native').is_socket():break
        time.sleep(.1)
    else:raise RuntimeError('Pulse did not start')
    env['PULSE_SERVER']='unix:'+str(runtime/'pulse/native')
    subprocess.run(['pactl','load-module','module-null-sink','sink_name=ci'],env=env,check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['pactl','set-default-sink','ci'],env=env,check=True)
    log=(out/'sunshine.log').open('w')
    children.append(subprocess.Popen(['/usr/bin/enclave-sunshine',str(config)],env=env,stdout=log,stderr=log))
    for i in range(120):
        assert all(c.poll() is None for c in children),'server exited'
        subprocess.run(['xsetroot','-solid','#c020c0' if i%2 else '#20c0c0'],check=True)
        time.sleep(2)
finally:
    for child in reversed(children):child.terminate()
    for child in children:
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait()
