#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
cp /packages/*.pub /etc/apk/keys/
printf '\n/packages/repository\n' >>/etc/apk/repositories
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
cp -a /src/aports/enclave-vpx-core /home/builder/aports/enclave/
cp /src/enclave-vpx-source.tar /home/builder/aports/enclave/enclave-vpx-core/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-vpx-core && abuild checksum && abuild -r' >/out/build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
cp /home/builder/aports/enclave/enclave-vpx-core/APKBUILD /out/APKBUILD
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-vpx-core
/usr/lib/enclave-os/vpinball/VPinballX_GL -v >/out/version.log 2>&1
