#!/bin/sh
set -eux
apk add --no-cache build-base json-c-dev
mkdir -p /out/transport
for name in prepass affine grid; do
    cc -O2 -g -std=c11 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all \
        "/src/components/shield-graphics/test_${name}_client.c" -ljson-c -o "/out/transport/$name"
    "/out/transport/$name"
done
