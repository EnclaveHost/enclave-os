#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3 xvfb-run xauth xdotool
cp /packages/*.pub /etc/apk/keys/
printf '\n/packages/repository\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-graphics
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
python3 /src/tools/stage-aports.py /home/builder/aports/enclave
for name in openhv; do
    cp -a "/src/aports/enclave-$name" /home/builder/aports/enclave/
done
cp /src/enclave-openhv-source.tar /home/builder/aports/enclave/enclave-openhv/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
for name in base cursor desktop openhv; do
    su builder -c "cd /home/builder/aports/enclave/enclave-$name && abuild checksum && abuild -r" >"/out/$name-build.log" 2>&1
    apk update
done
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
cp /home/builder/aports/enclave/enclave-openhv/APKBUILD /out/APKBUILD
apk add --no-cache enclave-openhv
chown builder:builder /out
export LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri LD_LIBRARY_PATH=/usr/lib/enclave-shield
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink
su builder -c 'xvfb-run -a -s "-screen 0 960x600x24 -nolisten tcp" python3 /src/tests/openhv-smoke.py'
