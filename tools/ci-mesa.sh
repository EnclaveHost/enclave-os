#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3 vulkan-tools mesa-utils xvfb-run xauth
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave /out
python3 /src/tools/stage-aports.py /home/builder/aports/enclave
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-shield-graphics && abuild -r' > /out/mesa-build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-graphics
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json
export VK_ICD_FILENAMES="$VK_DRIVER_FILES"
export LD_LIBRARY_PATH=/usr/lib/enclave-shield
export LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink
export LP_NUM_THREADS=1
vulkaninfo --summary > /out/vulkaninfo.txt 2>&1
xvfb-run -a -s '-screen 0 960x600x24 -nolisten tcp' glxinfo -B > /out/glxinfo.txt 2>&1
