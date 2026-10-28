#!/usr/bin/env python3
"""Test real package composition while the browser builds; emits no image."""
import json,pathlib,shutil,subprocess
source=pathlib.Path('/src');root=pathlib.Path('/out/dependency-test-root')
profile=json.loads((source/'profiles/common.json').read_text())
packages=sorted({p for f in profile['presets']['preview'] if f!='enclave-browser'
                 for p in profile['features'][f]}|{'xf86-video-dummy','enclave-native-platform'})
root.mkdir()
keys=pathlib.Path('/tmp/preview-all-keys');keys.mkdir()
for directory in (pathlib.Path('/etc/apk/keys'),pathlib.Path('/out/keys')):
    for key in directory.glob('*.pub'):shutil.copyfile(key,keys/key.name)
repos=pathlib.Path('/out/test-repositories')
repos.write_text('/out/repository\n'+pathlib.Path('/etc/apk/repositories').read_text())
subprocess.run(['apk','--root',str(root),'--initdb','--keys-dir',str(keys),
                '--repositories-file',str(repos),'--no-cache','add',*packages,'!py3-numpy-tests'],check=True)
with open('/out/package-composition.log','w') as log:
    subprocess.run(['chroot',str(root),'/bin/sh','-ec','''
        test "$(id -u desktop)" = 1000
        test "$(id -u shield)" = 1001
        test -x /usr/libexec/Xorg
        test -x /sbin/udevd
        test -x /usr/lib/enclave-shield-opencl/ir-compiler
        test -f /usr/lib/enclave-shield-opencl/gemm-reference.bc
        test -f /usr/lib/enclave-shield-opencl/q8-reference/mul_mv_q8_0_f32_flat.cl
        for command in enclave-openarena enclave-librequake enclave-vpinball enclave-openhv enclave-sunshine llama-cli sd-cli; do
            command -v "$command"
        done
        POCL_MAX_PTHREAD_COUNT=2 llama-cli --list-devices
        sd-cli --help
        /usr/lib/enclave-shield-hip/bin/hipcc --version
    '''],check=True,stdout=log,stderr=log,timeout=120)
shutil.copyfile(root/'lib/apk/db/installed','/out/preflight.apk-installed')
pathlib.Path('/out/preflight.json').write_text(json.dumps({'scope':'dependency-preflight-without-browser',
    'passed':True,'packages':packages,'browserPresent':False,'imageProduced':False,
    'runtimeAdmission':False,'productionQualified':False},indent=2)+'\n')
shutil.rmtree(root)
