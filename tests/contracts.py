#!/usr/bin/env python3
"""Catch lossy migration, policy regressions and architecture divergence."""
import hashlib,importlib.util,json,pathlib,re,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((root/'provenance/import.json').read_text())
for item in manifest['files']:
    assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
assert not (root/'reference/risc-box/guest/overlay/root/.ssh/authorized_keys').exists()
profile=json.loads((root/'profiles/common.json').read_text())
assert profile['resolution']==[960,600]
assert profile['default_preset']=='full'
assert {'freedoom','openarena','librequake','visual-pinball-x','openhv'}<=set(profile['presets'][profile['default_preset']])
assert {'enclave-browser','freedoom','agent','web-desktop'}<=set(profile['presets']['desktop'])
assert set(profile['presets']['minimal'])=={'core'}
assert set(profile['pending_features'])<=set(profile['presets']['full'])
assert (root/'aports/enclave-openarena/ioquake3-enclave.patch').read_bytes() == (root/'integrations/openarena/ioquake3-enclave.patch').read_bytes()
assert 'browser' not in profile['features']
assert profile['features']['enclave-browser']==['enclave-browser']
assert 'enclave-browser' not in profile['presets']['shell']
assert 'firefox-esr' not in (root/'components/desktop/bin/enclave-browser').read_text()
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
spec=importlib.util.spec_from_file_location('seed',root/'components/desktop/seed-home.py')
seed=importlib.util.module_from_spec(spec);spec.loader.exec_module(seed)
with tempfile.TemporaryDirectory() as td:
    home=pathlib.Path(td)/'home';home.mkdir(mode=0o700);(home/'.config').mkdir(mode=0o700)
    seed.seed(root/'components/desktop/skel',home)
    prefs=home/'.mozilla/firefox/enclave/user.js'
    assert prefs.is_file() and (home/'.config/gtk-3.0/settings.ini').is_file()
    prefs.write_text('user changes must survive login')
    seed.seed(root/'components/desktop/skel',home)
    assert prefs.read_text()=='user changes must survive login'
    assert (home.stat().st_mode & 0o777)==0o700
with tempfile.TemporaryDirectory() as td:
    subprocess.run(['python3',str(root/'tools/stage-aports.py'),td],check=True)
    blocked=subprocess.run(['python3',str(root/'tools/assemble.py'),'--arch','x86_64','--preset','full','--repository',td,'--key',td+'/test.pub','--output',td+'/root'],capture_output=True,text=True)
    assert blocked.returncode and 'Full feature parity is not qualified' in blocked.stderr
    for arch in ('x86_64','riscv64'):
        default=subprocess.run(['python3',str(root/'tools/assemble.py'),'--arch',arch,'--repository',td,'--key',td+'/test.pub','--output',td+'/root'],capture_output=True,text=True)
        assert default.returncode and 'Full feature parity is not qualified' in default.stderr
        assert all(game in default.stderr for game in ('openarena','librequake','visual-pinball-x','openhv'))
        assert not (pathlib.Path(td)/'root').exists()
print(f'PASS: {len(manifest["files"])} provenance hashes, shared feature graph, baseline policy, source archive checksums')
