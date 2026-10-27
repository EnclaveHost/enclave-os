#!/usr/bin/env python3
"""Reproducible component archives; verify committed checksums before building."""
import argparse, hashlib, io, pathlib, shutil, tarfile
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
    for component in ('base','cursor','desktop','freedoom'):
        name=f'enclave-{component}'; filename=f'{name}-0.1.0.tar'
        data=archive(component); checksum=hashlib.sha512(data).hexdigest()
        recipe=ROOT/'aports'/name/'APKBUILD'; text=recipe.read_text()
        expected=f'sha512sums="{checksum}  {filename}"\n'
        if args.update_checksums:
            text=text.split('sha512sums=')[0]+expected;recipe.write_text(text)
        elif expected not in text: raise SystemExit(f'{name}: source/checksum mismatch')
        target=args.destination/name;target.mkdir(parents=True,exist_ok=True)
        (target/filename).write_bytes(data);(target/'APKBUILD').write_text(text)
    shutil.copytree(ROOT/'aports/enclave-librequake',args.destination/'enclave-librequake',dirs_exist_ok=True)
if __name__=='__main__': main()
