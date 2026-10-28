#!/bin/sh
# Rebuild the shared desktop without recompiling unchanged game engines.
set -eux
apk add --no-cache alpine-sdk sudo python3 libx11-dev libxfixes-dev xvfb xauth xdotool mesa-dri-gallium
cp /baseline/*.pub /etc/apk/keys/
printf '\n/baseline/repository\n' >>/etc/apk/repositories
apk add --no-cache enclave-base enclave-cursor enclave-freedoom enclave-librequake
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
python3 /src/tools/stage-aports.py /home/builder/aports/enclave
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-desktop && abuild -r' >/out/build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache --upgrade enclave-desktop=0.1.0-r1
python3 - <<'PY'
import hashlib,json,pathlib
p=pathlib.Path('/usr/share/enclave-os/browser')
record=json.loads((p/'provenance.json').read_text())
assert hashlib.sha256((p/'ublock-origin.xpi').read_bytes()).hexdigest()==record['sha256']
policy=json.loads(pathlib.Path('/usr/lib/enclave-browser/distribution/policies.json').read_text())
assert policy['policies']['ExtensionSettings'][record['id']]['install_url']=='file:///usr/share/enclave-os/browser/ublock-origin.xpi'
PY
cc /src/tests/cursor-image.c -o /tmp/cursor-image -lX11 -lXfixes
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix
su builder -c 'python3 /src/tests/desktop-smoke.py' >/out/desktop-smoke.log 2>&1
