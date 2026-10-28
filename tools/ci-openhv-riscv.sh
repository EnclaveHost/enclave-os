#!/bin/sh
set -eux
apk add --no-cache python3 xvfb-run xauth xdotool icu-libs libgcc libstdc++ zlib libssl3 libcrypto3 lttng-ust libunwind krb5-libs sdl2 openal-soft freetype lua5.1-libs
cp /mesa/*.pub /etc/apk/keys/
printf '\n/mesa/repository\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-graphics
mkdir -p /opt/enclave-dotnet-candidate
set -- /runtime/out/packages/dotnet-runtime-*-linux-musl-riscv64.tar.gz
[ "$#" = 1 ]
tar -xf "$1" -C /opt/enclave-dotnet-candidate
python3 - <<'PY'
import json,pathlib
p=json.loads(pathlib.Path('/runtime/out/provenance.json').read_text())
assert p['commit']=='152ad965267240a3e23b6b3a24761e37aecc8c79'
assert p['target']=='linux-musl-riscv64'
PY
export DOTNET_EnableWriteXorExecute=1 COMPlus_EnableWriteXorExecute=1
export DOTNET_EnableDiagnostics=0 COMPlus_LTTng=0 DOTNET_ReadyToRun=0 COMPlus_ReadyToRun=0
/opt/enclave-dotnet-candidate/dotnet --info >/out/runtime-info.log 2>&1
/opt/enclave-dotnet-candidate/dotnet exec --fx-version 12.0.0-dev /managed/managed-runtime.dll >/out/managed-tests.log 2>&1
mkdir /tmp/game
set -- /game/repository/x86_64/enclave-openhv-[0-9]*.apk
[ "$#" = 1 ]
tar -xf "$1" -C /tmp/game
# Only the architecture-neutral managed payload is reused, never x86 libraries.
python3 - <<'PY'
from pathlib import Path
for p in Path('/tmp/game/usr/lib/enclave-os/openhv').rglob('*'):
 if p.is_file() and not p.is_symlink():
  assert p.read_bytes()[:4]!=b'\x7fELF',p
PY
mkdir -p /usr/lib/enclave-os /usr/libexec/enclave-os /etc/enclave-os
cp -a /tmp/game/usr/lib/enclave-os/openhv /usr/lib/enclave-os/
cp /src/components/desktop/game-env /usr/libexec/enclave-os/
cp /src/aports/enclave-openhv/settings.yaml /etc/enclave-os/openhv-settings.yaml
cp /src/aports/enclave-openhv/enclave-openhv /usr/bin/enclave-openhv
chmod 755 /usr/bin/enclave-openhv
cat >/usr/bin/dotnet <<'LAUNCH'
#!/bin/sh
exec /opt/enclave-dotnet-candidate/dotnet exec --fx-version 12.0.0-dev "$@"
LAUNCH
chmod 755 /usr/bin/dotnet
adduser -D -u 1000 player
chown player:player /out
export LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri LD_LIBRARY_PATH=/usr/lib/enclave-shield
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink
export ENCLAVE_GAME_START_TIMEOUT=300
su player -c 'xvfb-run -a -s "-screen 0 960x600x24 -nolisten tcp" python3 /src/tests/openhv-smoke.py'
