#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3 py3-pillow xvfb-run xauth xdotool fluxbox font-misc-misc font-dejavu xprop pulseaudio libx11-dev
for packages in /core /dependencies /mesa; do
    cp "$packages"/*.pub /etc/apk/keys/
    printf '\n%s/repository\n' "$packages" >>/etc/apk/repositories
done
apk add --no-cache enclave-vpx-core enclave-shield-graphics
adduser -D -u 2000 builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
python3 /src/tools/stage-aports.py /home/builder/aports/enclave
cp -a /src/aports/enclave-visual-pinball-x /home/builder/aports/enclave/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
for name in cursor desktop visual-pinball-x; do
    su builder -c "cd /home/builder/aports/enclave/enclave-$name && abuild -r" >"/out/$name-build.log" 2>&1
    apk update
done
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
apk add --no-cache enclave-visual-pinball-x
adduser -D -u 1000 player
cc -O2 /src/components/native-platform/desktop-capture.c -lX11 -o /tmp/capture
chown player:player /out
export LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri LD_LIBRARY_PATH=/usr/lib/enclave-shield
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json VK_ICD_FILENAMES=/usr/share/enclave-shield/vulkan/icd.json
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink LP_NUM_THREADS=2
su player -c 'xvfb-run -a -s "-screen 0 960x600x24 -nolisten tcp" python3 /src/tests/vpx-smoke.py'
