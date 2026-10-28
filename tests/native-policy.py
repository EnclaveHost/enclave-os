#!/usr/bin/env python3
"""Check recovered model-policy bindings without reading model payloads."""
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1])
record=json.loads((root/'recovered-source.json').read_text())
for name,digest in record['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
c=json.loads((root/'native-service.json').read_text())
assert c['schema']=='shield-guest-service/1'
assert c['sdk']=='/usr/lib/enclave-shield-compute'
assert c['core']=='/usr/lib/enclave-shield-service/libshield-core.so'
assert c['worker']=={'host':'unix:/run/shield-worker/gpu0','port':19595}
assert c['clientUids']==[1000,1003]
assert c['socket']=='/run/shield/compute.sock'
assert c['jobs']=='/run/shield/jobs'
assert set(c['models'])=={'llama','sd'}
for engine,spec in c['models'].items():
    policy=root/spec['policy'].removeprefix('/shield/')
    assert hashlib.sha256(policy.read_bytes()).hexdigest()==spec['policySha256']
    p=json.loads(policy.read_text())
    assert p['schema']=='shield-public-tensors/1'
    assert p['modelSha256']==spec['modelSha256']
    calibration=root/spec['calibration'].removeprefix('/shield/')
    assert hashlib.sha256(calibration.read_bytes()).hexdigest()==p['calibrationSha256']
    assert len({t['name'] for t in p['tensors']})==len(p['tensors'])
    assert spec['model'].startswith('/models/')
    print(engine, len(p['tensors']), 'public tensor policy/calibration bindings verified')
print('Model payloads, kernel execution and masked-worker numerical results remain unqualified.')
