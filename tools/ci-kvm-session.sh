#!/bin/sh
set -eux
apk add --no-cache build-base linux-headers go python3 git
mkdir -p /build/platform /out/compiled
cp -a /platform/isolation /build/platform/
export GOMAXPROCS=2 GOMEMLIMIT=1GiB CGO_ENABLED=0
for module in contract m2 m3; do
    (cd "/build/platform/isolation/$module" && go mod download)
done
python3 - <<'PY'
from pathlib import Path
p=Path('/build/platform/isolation/m3/monitor/native_kvm_test.go')
s=p.read_text()
old='nativeRootPath + "/usr/local/libexec/kvm-box/shield-desktop.wasm"'
assert s.count(old)==1
# The new immutable userland deliberately does not duplicate its controller.
# This change is confined to the explicitly selected Go test, never production.
p.write_text(s.replace(old, '"/probe-controller.wasm"'))
PY
(cd /build/platform/isolation/m3 && go test -c -mod=readonly -trimpath -buildvcs=false \
    -tags native_desktop -o /out/compiled/monitor-probe ./monitor)
cc -static -O2 -Wall -Wextra -Werror /src/tests/kvm-session/init.c -o /out/compiled/probe-init
cc -static -O2 -Wall -Wextra -Werror /src/tests/kvm-session/client.c -o /out/compiled/probe-native-client
python3 /src/tools/kvm_session_fixture.py /native /preview /out/compiled /inputs/controller.wasm /out/fixture
