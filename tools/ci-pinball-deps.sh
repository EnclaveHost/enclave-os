#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
for name in winevbs spatialaudio freeimage; do
    cp -a "/src/aports/enclave-$name" /home/builder/aports/enclave/
done
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
for name in winevbs spatialaudio freeimage; do
    su builder -c "cd /home/builder/aports/enclave/enclave-$name && abuild -r" >"/out/$name-build.log" 2>&1
done
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-winevbs enclave-spatialaudio enclave-freeimage
