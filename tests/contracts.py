#!/usr/bin/env python3
"""Catch lossy migration, policy regressions and architecture divergence."""
import hashlib,json,pathlib,re,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((root/'provenance/import.json').read_text())
for item in manifest['files']:
    assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
assert not (root/'reference/risc-box/guest/overlay/root/.ssh/authorized_keys').exists()
profile=json.loads((root/'profiles/common.json').read_text())
assert profile['resolution']==[960,600]
assert {'browser','freedoom','agent','web-desktop'}<=set(profile['presets']['desktop'])
assert set(profile['presets']['minimal'])=={'core'}
assert set(profile['pending_features'])<=set(profile['presets']['full'])
assert 'browser' not in profile['presets']['full'] # full image replaces upstream Firefox, not duplicates it
for arch in ('x86_64','riscv64'):
    p=json.loads((root/f'profiles/{arch}.json').read_text())
    assert p['architecture']==arch and not p['production_qualified']
    assert len(p['packages'])==1 # driver only; feature graph is architecture independent
prefs=(root/'components/desktop/skel/.mozilla/firefox/enclave/user.js').read_text()
for forbidden in ('fission.autostart", false','security.OCSP.enabled','security.ssl3','browser.safebrowsing','accessibility.force_disabled','image.animation_mode','network.http.http3.enable'):
    assert forbidden not in prefs,forbidden
assert 'kernel.randomize_va_space = 2' in (root/'components/base/etc/sysctl.d/50-enclave.conf').read_text()
for path in (root/'components').rglob('*'):
    if path.is_file() and path.suffix in ('.py','.sh'):
        assert '--allow-untrusted' not in path.read_text()
with tempfile.TemporaryDirectory() as td:
    subprocess.run(['python3',str(root/'tools/stage-aports.py'),td],check=True)
    blocked=subprocess.run(['python3',str(root/'tools/assemble.py'),'--arch','x86_64','--preset','full','--repository',td,'--key',td+'/test.pub','--output',td+'/root'],capture_output=True,text=True)
    assert blocked.returncode and 'Full feature parity is not qualified' in blocked.stderr
print(f'PASS: {len(manifest["files"])} provenance hashes, shared feature graph, baseline policy, source archive checksums')
