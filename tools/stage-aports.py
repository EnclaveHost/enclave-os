#!/usr/bin/env python3
"""Reproducible component archives; verify committed checksums before building."""
import argparse, hashlib, io, pathlib, shutil, tarfile, re
ROOT = pathlib.Path(__file__).resolve().parents[1]

def archive(component):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w', format=tarfile.GNU_FORMAT) as tar:
        for p in sorted((ROOT / 'components' / component).rglob('*')):
            if '__pycache__' in p.parts: continue
            info = tar.gettarinfo(str(p), f'enclave-{component}-0.1.0/{p.relative_to(ROOT / "components" / component)}')
            info.uid = info.gid = info.mtime = 0
            info.uname = info.gname = ''
            info.mode = 0o755 if p.is_dir() or p.stat().st_mode & 0o111 else 0o644
            if p.is_file():
                with p.open('rb') as src: tar.addfile(info, src)
            else: tar.addfile(info)
    return data.getvalue()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('destination', type=pathlib.Path)
    parser.add_argument('--update-checksums', action='store_true');args=parser.parse_args()
    for component in ('base','cursor','desktop','freedoom','shield-graphics'):
        name=f'enclave-{component}'; filename=f'{name}-0.1.0.tar'
        data=archive(component); checksum=hashlib.sha512(data).hexdigest()
        recipe=ROOT/'aports'/name/'APKBUILD'; text=recipe.read_text()
        expected=f'{checksum}  {filename}'
        if args.update_checksums:
            text,count=re.subn(r'(?:[a-f0-9]{128}|PLACEHOLDER)(?=  '+re.escape(filename)+r'(?:"|\n))',checksum,text)
            if count != 1: raise SystemExit(f'{name}: expected one source checksum')
            recipe.write_text(text)
        elif expected not in text: raise SystemExit(f'{name}: source/checksum mismatch')
        target=args.destination/name;target.mkdir(parents=True,exist_ok=True)
        (target/filename).write_bytes(data);(target/'APKBUILD').write_text(text)
    for name in ('enclave-librequake','enclave-openarena'):
        shutil.copytree(ROOT/'aports'/name,args.destination/name,dirs_exist_ok=True)
if __name__=='__main__': main()
