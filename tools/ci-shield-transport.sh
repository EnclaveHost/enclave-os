#!/bin/sh
set -eux
apk add --no-cache build-base json-c-dev
mkdir -p /out/transport
sanitize="-fsanitize=undefined -fno-sanitize-recover=all"
if [ "$(apk --print-arch)" = riscv64 ]; then
    # Alpine RV64 has no libubsan package; retain checks as immediate traps.
    sanitize="$sanitize -fsanitize-undefined-trap-on-error"
fi
for name in prepass affine grid; do
    cc -O2 -g -std=c11 -Wall -Wextra -Werror $sanitize \
        "/src/components/shield-graphics/test_${name}_client.c" -ljson-c -o "/out/transport/$name"
    "/out/transport/$name"
done
