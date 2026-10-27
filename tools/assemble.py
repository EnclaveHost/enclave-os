#!/usr/bin/env python3
"""Assemble a clean Alpine userland. Kernel/attestation adapters are separate."""
import argparse, hashlib, json, pathlib, shutil, subprocess, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(*args): subprocess.run(args,check=True)
def main():
    profile=json.loads((ROOT/'profiles/common.json').read_text())
    p=argparse.ArgumentParser()
    p.add_argument('--arch',choices=['x86_64','riscv64'],required=True)
    p.add_argument('--preset',choices=list(profile['presets']),default=profile['default_preset'],help='default: full shared image; minimal/desktop are explicit development subsets')
    p.add_argument('--repository',type=pathlib.Path,required=True,help='signed local repository parent (contains architecture dirs)')
    p.add_argument('--key',type=pathlib.Path,required=True,help='public APK signing key ONLY')
    p.add_argument('--output',type=pathlib.Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if out.exists(): p.error('output must not exist; refusing to modify an existing root')
    if not a.key.name.endswith('.pub'): p.error('only a public signing key may enter an image')
    lock=json.loads((ROOT/'profiles/upstream-lock.json').read_text())
    platform=json.loads((ROOT/f'profiles/{a.arch}.json').read_text())
    missing=[feature for feature in profile['presets'][a.preset] if feature not in profile['features']]
    if missing:p.error('Full feature parity is not qualified: '+', '.join(missing))
    packages=sorted(set(pkg for feature in profile['presets'][a.preset] for pkg in profile['features'][feature]))
    if 'desktop' in profile['presets'][a.preset]: packages+=platform['packages']
    url=f'https://dl-cdn.alpinelinux.org/alpine/{lock["alpine_branch"]}/releases/{a.arch}/alpine-minirootfs-{lock["alpine_version"]}-{a.arch}.tar.gz'
    data=urllib.request.urlopen(url,timeout=60).read()
    if hashlib.sha256(data).hexdigest()!=lock['minirootfs'][a.arch]['sha256']: raise SystemExit('minirootfs checksum mismatch')
    out.parent.mkdir(parents=True,exist_ok=True);out.mkdir()
    tarpath=out.parent/(out.name+'.bootstrap.tar.gz');tarpath.write_bytes(data)
    run('tar','-xzf',str(tarpath),'-C',str(out));tarpath.unlink()
    shutil.copyfile(a.key,out/'etc/apk/keys'/a.key.name)
    # Trust remains enforced: neither package nor index verification is bypassed.
    repos=out.parent/(out.name+'.build-repositories')
    upstream=[f'https://dl-cdn.alpinelinux.org/alpine/{lock["alpine_branch"]}/{c}' for c in ('main','community')]
    repos.write_text('\n'.join([str(a.repository.resolve()),*upstream])+'\n')
    run('apk','--root',str(out),'--arch',a.arch,'--keys-dir',str(out/'etc/apk/keys'),'--repositories-file',str(repos),'--no-cache','add',*packages,*('!'+name for name in profile['exclude_packages']))
    repos.unlink();(out/'etc/apk/repositories').write_text('\n'.join(upstream)+'\n')
    # CI keys authorize this test artifact only, never a production feed.
    (out/'etc/apk/keys'/a.key.name).unlink()
    if 'desktop' in profile['presets'][a.preset]:
        target=out/'etc/X11/xorg.conf';target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'platforms'/platform['platform']/'xorg.conf',target)
    installed=(out/'lib/apk/db/installed').read_text()
    sizes=[]
    for block in installed.split('\n\n'):
        fields=dict(line.split(':',1) for line in block.splitlines() if ':' in line)
        if 'P' in fields:
            assert fields['P'] not in profile['exclude_packages']
            sizes.append({'package':fields['P'],'bytes':int(fields.get('I','0'))})
    sizes.sort(key=lambda item:item['bytes'],reverse=True)
    report={'largest_packages':sizes[:20],'excluded_test_packages':profile['exclude_packages'],'architecture':a.arch,'preset':a.preset,'platform':platform['platform'],'production_qualified':False,
            'requested_packages':packages,'bytes':sum(f.stat().st_size for f in out.rglob('*') if f.is_file() and not f.is_symlink())}
    # Installed database records dependency versions, sizes and origin for the entire image.
    shutil.copyfile(out/'lib/apk/db/installed',out.parent/(out.name+'.apk-installed'))
    (out.parent/(out.name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
