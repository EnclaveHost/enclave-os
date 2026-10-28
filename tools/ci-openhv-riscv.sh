#!/bin/sh
set -eux
apk add --no-cache python3 xvfb-run xauth xdotool icu-libs libgcc libstdc++ zlib libssl3 libcrypto3 lttng-ust libunwind krb5-libs sdl2 openal-soft freetype lua5.1-libs
cp /mesa/*.pub /etc/apk/keys/
printf '\n/mesa/repository\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-graphics
python3 - <<'PYCODE'
import json,pathlib
p=json.loads(pathlib.Path('/runtime/out/provenance.json').read_text())
assert p['commit']=='152ad965267240a3e23b6b3a24761e37aecc8c79'
assert p['target']=='linux-musl-riscv64'
PYCODE
apk add --no-cache alpine-sdk sudo
adduser -D -u 2000 builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
python3 /src/tools/stage-aports.py /home/builder/aports/enclave
for name in dotnet-riscv openhv-riscv; do
    cp -a "/src/aports/enclave-$name" /home/builder/aports/enclave/
done
set -- /runtime/out/packages/dotnet-runtime-*-linux-musl-riscv64.tar.gz
[ "$#" = 1 ]
cp "$1" /home/builder/aports/enclave/enclave-dotnet-riscv/dotnet-runtime.tar.gz
cp /runtime/out/provenance.json /home/builder/aports/enclave/enclave-dotnet-riscv/runtime-provenance.json
cp /game/*.pub /etc/apk/keys/
set -- /game/repository/x86_64/enclave-openhv-[0-9]*.apk
[ "$#" = 1 ]
apk verify "$1"
cp "$1" /home/builder/aports/enclave/enclave-openhv-riscv/enclave-openhv-managed.apk
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
for name in cursor desktop dotnet-riscv openhv-riscv; do
    su builder -c "cd /home/builder/aports/enclave/enclave-$name && abuild checksum && abuild -r" >"/out/$name-build.log" 2>&1
    apk update
done
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
for name in dotnet-riscv openhv-riscv; do
    cp "/home/builder/aports/enclave/enclave-$name/APKBUILD" "/out/$name.APKBUILD"
done
apk add --no-cache enclave-openhv-riscv
export DOTNET_EnableWriteXorExecute=1 COMPlus_EnableWriteXorExecute=1
export DOTNET_EnableDiagnostics=0 COMPlus_LTTng=0 DOTNET_ReadyToRun=0 COMPlus_ReadyToRun=0
/usr/lib/enclave-dotnet/dotnet --info >/out/runtime-info.log 2>&1
/usr/lib/enclave-dotnet/dotnet exec --fx-version 12.0.0-dev /managed/managed-runtime.dll >/out/managed-tests.log 2>&1
adduser -D -u 1000 player
chown player:player /out
export LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri LD_LIBRARY_PATH=/usr/lib/enclave-shield
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink
export ENCLAVE_GAME_START_TIMEOUT=300
su player -c 'xvfb-run -a -s "-screen 0 960x600x24 -nolisten tcp" python3 /src/tests/openhv-smoke.py'
