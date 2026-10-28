#!/usr/bin/env python3
"""Pair real Moonlight to isolated musl Sunshine and inspect decoded frames."""
import base64,json,os,pathlib,secrets,ssl,subprocess,time,urllib.request
from PIL import ImageGrab
root=pathlib.Path.cwd();fixture=root/'fixture';out=root/'out'
home=fixture/'client-home';home.mkdir()
env={**os.environ,'HOME':str(home),'XDG_CONFIG_HOME':str(home/'config'),
     'QT_QUICK_BACKEND':'software','SDL_AUDIODRIVER':'dummy',
     'QT_LOGGING_RULES':'qt.*.debug=false'}
password=(fixture/'password').read_text()
context=ssl.create_default_context(cafile=str(fixture/'cert.pem'))
auth='Basic '+base64.b64encode(('ci:'+password).encode()).decode()
def api(path,data=None):
    headers={'Authorization':auth}
    body=None
    if data is not None:headers['Content-Type']='application/json';body=json.dumps(data).encode()
    req=urllib.request.Request('https://localhost:47990'+path,data=body,headers=headers)
    with urllib.request.urlopen(req,context=context,timeout=3) as r:return json.load(r)
deadline=time.monotonic()+120
while True:
    try:api('/api/pin');break
    except Exception:
        if time.monotonic()>deadline:raise
        time.sleep(1)
pin=f'{secrets.randbelow(10000):04d}'
client=str(root/'client/moonlight')
with (out/'pair.log').open('w') as pair_log:
    pair=subprocess.Popen([client,'pair','127.0.0.1','--pin',pin],env=env,stdout=pair_log,stderr=pair_log)
    try:
        for _ in range(60):
            pending=api('/api/pin')['pairings']
            if pending:
                assert len(pending)==1
                assert api('/api/pin',{'pairing_id':pending[0]['id'],'pin':pin,'name':'Enclave CI'})['status'] is True
                break
            assert pair.poll() is None
            time.sleep(.5)
        else:raise AssertionError('No pending pairing')
        for _ in range(40):
            if api('/api/clients/list')['named_certs']:break
            time.sleep(.25)
        else:raise AssertionError('Server did not retain paired client')
        # Qt's CLI pairing action presents a success dialog. Acknowledge that
        # dialog only after the server confirms cryptographic pairing.
        time.sleep(1)
        windows=subprocess.check_output(['xdotool','search','--onlyvisible','--pid',str(pair.pid)],text=True).splitlines()
        subprocess.run(['xdotool','windowfocus',windows[-1],'key','Return'],check=True)
        assert pair.wait(timeout=10)==0
    finally:
        if pair.poll() is None:pair.kill();pair.wait()
with (out/'stream.log').open('w') as log:
    stream=subprocess.Popen([client,'stream','127.0.0.1','Enclave CI Desktop',
        '--resolution','960x600','--fps','30','--bitrate','5000',
        '--display-mode','windowed','--video-decoder','software','--video-codec','H.264',
        '--no-vsync','--no-mute-on-focus-loss'],env=env,stdout=log,stderr=log)
    seen=set();counts=[]
    try:
        for index in range(60):
            assert stream.poll() is None,'client exited before decoded frame checks'
            frame=ImageGrab.grab(xdisplay=os.environ['DISPLAY']).convert('RGB')
            magenta=cyan=0
            for r,g,b in frame.resize((256,192)).getdata():
                magenta+=r>130 and b>130 and g<100
                cyan+=g>130 and b>130 and r<100
            counts.append([magenta,cyan])
            for name,count in [('magenta',magenta),('cyan',cyan)]:
                if count>18000 and name not in seen:
                    seen.add(name);frame.save(out/f'decoded-{name}.png')
            if len(seen)==2 and index>=10:break
            time.sleep(1)
        assert seen=={'magenta','cyan'},counts
        (out/'stream-results.json').write_text(json.dumps({'authenticatedPairing':True,
            'sunshineRequiresEncryptedStream':True,'decodedChangingDesktop':True,
            'resolution':[960,600],'colorsObserved':sorted(seen),'sampleCounts':counts,
            'audioContinuityQualified':False,'nativeAdapterQualified':False},indent=2)+'\n')
    finally:
        stream.terminate()
        try:stream.wait(timeout=10)
        except subprocess.TimeoutExpired:stream.kill();stream.wait()
