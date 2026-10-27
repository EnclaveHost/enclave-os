#!/usr/bin/env python3
"""Record compressed sizes and checksums after native-runner compression."""
import hashlib,json,pathlib
out=pathlib.Path('out')
rows=[]
for p in sorted(out.glob('*-rootfs.tar.gz')):
    preset=p.name.removesuffix('-rootfs.tar.gz').rsplit('-',1)[-1]
    report=out/f'root-{preset}.json'
    data=json.loads(report.read_text())
    with p.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
    data['archive']={'name':p.name,'bytes':p.stat().st_size,'sha256':digest}
    report.write_text(json.dumps(data,indent=2)+'\n')
    rows.append(f'{digest}  {p.name}')
    print(f'{data["architecture"]} {preset}: {data["bytes"]} installed bytes; {p.stat().st_size} compressed bytes')
(out/'SHA256SUMS').write_text('\n'.join(rows)+'\n')
