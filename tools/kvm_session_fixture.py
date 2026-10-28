"""Append explicit test programs to the unchanged native platform archive."""
import base64
import gzip
import hashlib
import json
import pathlib
import stat
import struct
import sys


def build(platform, preview, compiled, controller, output):
    platform, preview, compiled, controller, output = map(pathlib.Path, (platform, preview, compiled, controller, output))
    output.mkdir(parents=True, exist_ok=False)
    sha = lambda b: hashlib.sha256(b).hexdigest()
    base = (platform/'platform/native.cpio.gz').read_bytes()
    record = json.loads((platform/'platform/build.json').read_text())
    assert sha(base) == record['initrd']['sha256']
    raw = (preview/'kvm-profile.json').read_bytes()
    profile = json.loads(raw)
    assert sha(raw) == record['inputPins']['profile']['sha256']
    artifact = controller.read_bytes()
    assert sha(artifact) == profile['controllerSha256']
    entries = {name: ((compiled/name).read_bytes(), stat.S_IFREG | 0o555)
               for name in ('probe-init', 'probe-native-client', 'monitor-probe')}
    entries['probe-controller.wasm'] = (artifact, stat.S_IFREG | 0o444)
    buf = bytearray()
    for ino, (name, (data, mode)) in enumerate(sorted(entries.items())+[('TRAILER!!!', (b'', 0))], 60000):
        label = name.encode()+b'\0'
        fields = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(label), 0]
        buf += b'070701'+b''.join(f'{x:08x}'.encode() for x in fields)+label
        buf += b'\0'*(-len(buf) % 4)
        buf += data
        buf += b'\0'*(-len(buf) % 4)
    buf += b'\0'*(-len(buf) % 512)
    test = base+gzip.compress(bytes(buf), mtime=0)
    (output/'probe.cpio.gz').write_bytes(test)
    manifest = {'abi': 'enclave-domain-abi/1', 'artifact': {'kind': 'wasm-component', 'sha256': sha(artifact)},
                'world': 'wasi:cli', 'http': 8000,
                'ports': ['tcp:47984', 'tcp:47989', 'tcp:48010', 'udp:47998', 'udp:47999', 'udp:48000'],
                'policy': {'cpuPercent': 400, 'memMiB': 8192, 'vcpus': 4},
                'desktop': {'profile': 'kvm-box-masked-v1', 'profileSha256': sha(raw), 'gpuMilli': 500},
                'secretDeployment': '0x'+'1'*64, 'configBase64': base64.b64encode(b'{"egress":"public-web"}').decode()}
    encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    bundle = b'ENCLAVE-BUNDLE/1\n'+struct.pack('<I', len(encoded))+encoded+struct.pack('<I', len(artifact))+artifact
    result = {'schema': 'enclave-os-native-session-fixture/1', 'disposableFixtureOnly': True,
              'productionInitrdSha256': sha(base), 'initrdSha256': sha(test), 'profileSha256': sha(raw),
              'expect': {'appID': sha(bundle), 'profileSHA': sha(raw), 'gpuMilli': 500},
              'addedFiles': {name: sha(data) for name, (data, _) in entries.items()},
              'scope': 'Actual native services and lifecycle; privileged fixture client; synthetic worker; no owner secrets, controller execution or GPU work'}
    (output/'fixture.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    build(*sys.argv[1:])
