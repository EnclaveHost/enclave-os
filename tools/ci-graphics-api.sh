#!/bin/sh
set -eux
apk add --no-cache build-base python3 vulkan-loader-dev mesa-dev libx11-dev glslang spirv-tools xvfb-run xauth
cp /packages/*.pub /etc/apk/keys/
printf '\n/packages/repository\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-graphics
export VK_DRIVER_FILES=/usr/share/enclave-shield/vulkan/icd.json VK_ICD_FILENAMES=/usr/share/enclave-shield/vulkan/icd.json
export LD_LIBRARY_PATH=/usr/lib/enclave-shield LIBGL_DRIVERS_PATH=/usr/lib/enclave-shield/dri
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=zink MESA_LOADER_DRIVER_OVERRIDE=zink LP_NUM_THREADS=1
export XDG_RUNTIME_DIR=/tmp/runtime
mkdir -m700 "$XDG_RUNTIME_DIR"
src=/src/components/shield-graphics/qualification
OUTPUT=/out/api sh "$src/build.sh"
c++ -std=c++17 -O2 -Wall -Wextra -Werror "$src/prepass-gl.cpp" -lGL -lX11 -o /out/api/prepass-gl
c++ -std=c++17 -O2 -Wall -Wextra -Werror "$src/glx-robustness.cpp" -lGL -lX11 -o /out/api/glx-robustness
python3 /src/tests/graphics-abi.py
