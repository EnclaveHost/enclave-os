#!/bin/sh
set -eux
apk add --no-cache build-base python3 py3-pillow xvfb-run xauth xdotool fluxbox pulseaudio libx11-dev
for packages in /core /dependencies /mesa; do
    cp "$packages"/*.pub /etc/apk/keys/
    printf '\n%s/repository\n' "$packages" >>/etc/apk/repositories
done
apk add --no-cache enclave-vpx-core enclave-shield-graphics
adduser -D player
cc -O2 /src/components/native-platform/desktop-capture.c -lX11 -o /tmp/capture
chown player:player /out
export LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri LD_LIBRARY_PATH=/usr/lib/enclave-shield
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json VK_ICD_FILENAMES=/usr/share/enclave-shield/vulkan/icd.json
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink LP_NUM_THREADS=2
su player -c 'xvfb-run -a -s "-screen 0 960x600x24 -nolisten tcp" python3 /src/tests/vpx-smoke.py'
