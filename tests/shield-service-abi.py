#!/usr/bin/env python3
"""Installed musl ABI and socket boundary; never connects to a GPU worker."""
import ctypes as C
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading

root = Path('/usr/lib/enclave-shield-service')
sys.path.insert(0, str(root))
from service import Compute, Server, Handler, send, receive

assert os.geteuid() == 0, 'isolated CI container must run this UID fixture as root'
libpath = root / 'libshield-core.so'
lib = C.CDLL(str(libpath))
lib.sh_pipe_open.argtypes = [C.c_char_p, C.c_int, C.POINTER(C.c_int)]
lib.sh_pipe_open.restype = C.c_void_p
receipt = {}
with tempfile.TemporaryDirectory() as directory:
    os.chmod(directory, 0o777)
    endpoint = str(Path(directory) / 'untrusted.sock')
    ready, signal = os.pipe()
    child = os.fork()
    if child == 0:
        try:
            os.close(ready)
            os.setgroups([])
            os.setgid(1001)
            os.setuid(1001)
            with socket.socket(socket.AF_UNIX) as listener:
                listener.settimeout(10)
                listener.bind(endpoint)
                listener.listen(1)
                os.write(signal, b'R')
                with listener.accept()[0] as conn:
                    conn.settimeout(10)
                    assert conn.recv(1) == b'', 'sent protocol bytes to untrusted broker'
            os._exit(0)
        except BaseException:
            os._exit(1)
    os.close(signal)
    assert os.read(ready, 1) == b'R'
    os.close(ready)
    error = C.c_int()
    result = lib.sh_pipe_open(('unix:' + endpoint).encode(), 0, C.byref(error))
    assert not result and error.value != 0, 'wrong broker UID admitted'
    assert os.waitpid(child, 0)[1] == 0
    receipt['wrongBrokerUidRejectedBeforeBytes'] = True

    endpoint = str(Path(directory) / 'service.sock')
    config = dict(schema='shield-guest-service/1', models={}, clientUids=[1000])
    with Server(endpoint, Handler) as server:
        server.compute = Compute(config)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(5)
                client.connect(endpoint)
                assert client.recv(1) == b'', 'service accepted unlisted UID'
            receipt['clientUidAclEnforced'] = True
            config['clientUids'] = [0]
            with socket.socket(socket.AF_UNIX) as client:
                client.settimeout(5)
                client.connect(endpoint)
                send(client, {'op': 'status'})
                response = receive(client, 1 << 20)
                assert response['ok'] is True, response
            receipt['allowedClientStatus'] = True
        finally:
            server.shutdown()
            thread.join(timeout=5)

dynamic = subprocess.check_output(['readelf', '-d', str(libpath)], text=True).lower()
assert not any(name in dynamic for name in ('libcuda', 'libvulkan', 'libdrm'))
segments = subprocess.check_output(['readelf', '-lW', str(libpath)], text=True)
assert not any('GNU_STACK' in line and 'RWE' in line for line in segments.splitlines())
receipt['noRawGpuDependencyOrExecutableStack'] = True
receipt['maskedGpuExecutionQualified'] = False
print(json.dumps(receipt, indent=2))
