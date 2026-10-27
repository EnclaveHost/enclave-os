#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave/enclave-sunshine /out
cp /src/aports/enclave-sunshine/APKBUILD /home/builder/aports/enclave/enclave-sunshine/
cp /src/enclave-sunshine-source.tar /home/builder/aports/enclave/enclave-sunshine/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-sunshine && abuild checksum && abuild -r' > /out/sunshine-build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
cp /home/builder/aports/enclave/enclave-sunshine/APKBUILD /out/APKBUILD
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-sunshine
/usr/bin/enclave-sunshine --version > /out/version.txt 2>&1
