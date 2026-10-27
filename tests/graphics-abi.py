#!/usr/bin/env python3
"""Exercise real Vulkan/GL entry points; no GPU execution is claimed."""
import json, os, pathlib, socket, subprocess, threading
out=pathlib.Path('/out/api')
def run(name, command):
    with (out/(name+'.log')).open('w') as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
run('vulkan-cpu', [str(out/'prepass'),str(out),str(out/'triangle.rgba')])
run('gl-compute', ['xvfb-run','-a','-s','-screen 0 960x600x24 -nolisten tcp',str(out/'prepass-gl'),'/src/components/shield-graphics/qualification/prepass-gl.comp'])
run('gl-robustness', ['xvfb-run','-a',str(out/'glx-robustness')])
root=pathlib.Path('/run/shield');root.mkdir(mode=0o755)
server=socket.socket(socket.AF_UNIX);server.bind(str(root/'compute.sock'));server.listen(1);server.settimeout(20)
received=[];errors=[]
def reject_peer():
    try:
        connection,_=server.accept()
        with connection:
            connection.settimeout(10)
            received.append(connection.recv(1))
    except Exception as e: errors.append(str(e))
thread=threading.Thread(target=reject_peer);thread.start()
try:
    # The service socket is owned by root, rather than the required Shield uid.
    run('vulkan-wrong-peer', [str(out/'prepass'),str(out),str(out/'must-not-publish.rgba'),'--expect-device-lost'])
    thread.join(25)
    assert not thread.is_alive() and not errors and received==[b''], (received,errors)
    assert not (out/'must-not-publish.rgba').exists()
finally:
    server.close();(root/'compute.sock').unlink();root.rmdir()
(out/'results.json').write_text(json.dumps({'cpuShaderAndDraw':True,'openGLCompute':True,'robustContext':True,'wrongPeerRejectedBeforeRequest':True,'gpuExecution':False},indent=2)+'\n')
