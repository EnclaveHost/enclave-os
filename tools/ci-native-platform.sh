#!/bin/sh
set -eux
apk add --no-cache build-base linux-headers libx11-dev python3 go
mkdir -p /build /out/bin
cp -a /src/components/native-platform/. /build/
cd /build
python3 - <<'PY'
import hashlib,json,pathlib
root=pathlib.Path('/src/components/desktop/skel')
files=[]
for p in sorted(root.rglob('*')):
    if p.is_symlink(): raise ValueError('shared skeleton contains a link')
    if p.is_file():
        data=p.read_bytes()
        files.append({'path':str(p.relative_to(root)),'bytes':len(data),
                      'sha256':hashlib.sha256(data).hexdigest(),'mode':0o644})
pathlib.Path('home-defaults-manifest.json').write_text(json.dumps({
    'schema':'kvm-box-native-home-defaults/1','files':files},indent=2)+'\n')
PY
python3 build_home_defaults.py --root /src/components/desktop/skel \
    --manifest home-defaults-manifest.json --output home-defaults.h
for name in nsinit supervisor udev-launch; do
    cc -O2 -Wall -Wextra -Werror -fstack-protector-strong -fPIE -pie \
        -DKVMBOX_SHIELD_GRAPHICS -I/src/components/platform-policy \
        "$name.c" -Wl,-z,relro,-z,now,-z,noexecstack -o "/out/bin/$name"
done
cc -O2 -Wall -Wextra -Werror desktop-capture.c -lX11 \
    -Wl,-z,relro,-z,now,-z,noexecstack -o /out/bin/capture
export GO111MODULE=off GOMAXPROCS=2
go test -race -timeout 180s -v ./gateway ./inner ./automation >/out/protocol-tests.log 2>&1
go vet ./gateway ./inner ./automation >/out/vet.log 2>&1
for name in gateway inner automation; do
    CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o "/out/bin/$name" "./$name"
done
python3 - <<'PY'
import hashlib,json,pathlib,subprocess
for command in (['/out/bin/nsinit','invalid'],['/out/bin/supervisor'],['/out/bin/udev-launch','invalid']):
    result=subprocess.run(command,timeout=5)
    assert result.returncode==64,(command,result.returncode)
roots=[pathlib.Path('/src/components/native-platform'),pathlib.Path('/src/components/platform-policy'),
       pathlib.Path('/src/components/desktop/skel')]
files={str(p.relative_to('/src')):hashlib.sha256(p.read_bytes()).hexdigest()
       for root in roots for p in sorted(root.rglob('*')) if p.is_file()}
pathlib.Path('/out/provenance.json').write_text(json.dumps({'sourceFiles':files,
    'binaries':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/out/bin').iterdir()},
    'releaseQualified':False,'target':'x86_64-alpine-linux-musl'},indent=2)+'\n')
PY
cp home-defaults-manifest.json /out/
