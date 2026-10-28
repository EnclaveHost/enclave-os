#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo linux-headers libx11-dev python3 go novnc=1.6.0-r1 nodejs
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
    cc -O2 -Wall -Wextra -Werror -fstack-protector-strong -fPIE -static-pie \
        -DKVMBOX_SHIELD_GRAPHICS -I/src/components/platform-policy \
        "$name.c" -Wl,-z,relro,-z,now,-z,noexecstack -o "/out/bin/$name"
    # These run before pivoting into the musl desktop root. They must not
    # depend on the old platform's glibc interpreter or a second loader copy.
    if readelf -lW "/out/bin/$name" | grep -q INTERP; then exit 1; fi
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
node --test desktop-pacing.test.mjs >/out/desktop-pacing-tests.log 2>&1
python3 build_ui_assets.py --novnc /usr/share/novnc --native-page native.html --output /build/ui
mkdir -p /build/native-platform/bin
cp /out/bin/* /build/native-platform/bin/
cp -a /build/ui /build/native-platform/ui
python3 /src/tests/native-policy.py /build/shield
cp -a /build/shield /build/native-platform/shield
python3 - <<'PY'
import pathlib,json,hashlib
root=pathlib.Path('/build/licenses/novnc')
for name,digest in json.loads((root/'provenance.json').read_text())['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
PY
cp -a /build/licenses /build/native-platform/licenses
cp readiness.py network_policy.py 70-kvm-box-input.rules sunshine.conf sunshine-apps.json /build/native-platform/
cp /src/platforms/kvm-box/xorg.conf /build/native-platform/xorg.conf
cp /src/LICENSE /build/native-platform/LICENSE
cp /out/provenance.json /build/native-platform/
adduser -D -u 2000 builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
cp -a /src/aports/enclave-native-platform /home/builder/aports/enclave/
tar -cf /home/builder/aports/enclave/enclave-native-platform/native-platform.tar -C /build native-platform
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
apk update
su builder -c 'cd /home/builder/aports/enclave/enclave-native-platform && abuild checksum && abuild -r' >/out/package-build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-native-platform
test "$(id -u desktop)" = 1000
test "$(id -u shield)" = 1001
test -x /usr/libexec/Xorg
test -x /sbin/udevd
test -x /usr/sbin/nft
/usr/sbin/nft --version >/out/installed-nft-version.log
test -f /usr/share/enclave-os/native-ui/novnc/vnc.html
test -f /usr/share/enclave-os/native-ui/novnc/app/native-pacing.mjs
python3 /src/tests/native-policy.py /shield >/out/installed-model-policy.log
stat -c '%a %u %g %n' /desktop.profile /usr/libexec/enclave-os/native/* >/out/installed-boundary.log
