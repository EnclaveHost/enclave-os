#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo texinfo dejagnu linux-headers python3 strace
mkdir -p /out
cc -O2 -Wall -Wextra -Werror -I/src/components/platform-policy \
    /src/tests/managed-policy-exec.c -o /out/policy-exec
# Retain the stock behavior for diagnosis; acceptance uses the rebuilt package.
strace -f -o /out/stock-ffi.trace /out/policy-exec /usr/bin/python3 -I -c 'import ctypes' \
    >/out/stock-ffi.log 2>&1 || true
adduser -D -u 2000 builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
cp -a /src/aports/libffi /home/builder/aports/enclave/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/libffi && abuild -r' >/out/package-build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
apk add --no-cache /out/repository/x86_64/libffi-3.5.2-r100.apk
/out/policy-exec /usr/bin/python3 -I /src/tests/ffi-policy.py >/out/ffi-policy.json
