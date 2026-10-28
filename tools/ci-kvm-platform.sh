#!/bin/sh
set -eux
apk add --no-cache python3 build-base linux-headers go git
mkdir -p /build/platform
cp -a /platform/isolation /build/platform/
export GOMAXPROCS=2 GOMEMLIMIT=1GiB
for module in contract m2 m3; do
    (cd "/build/platform/isolation/$module" && go mod download)
done
python3 /src/tools/kvm_platform_spec.py /preview /retained /out/platform-spec.json
python3 /build/platform/isolation/m3/build-native.py --spec /out/platform-spec.json --out /out/platform
python3 /src/tools/kvm_archive_check.py /out/platform /out/platform-spec.json
