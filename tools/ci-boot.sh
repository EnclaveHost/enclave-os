#!/bin/sh
# Native x86-64 harness: emulate either target CPU, without /dev/kvm or host mounts.
set -eu
apk add --no-cache python3 "qemu-system-$ENCLAVE_ARCH"
"qemu-system-$ENCLAVE_ARCH" --version
python3 /src/tests/boot-smoke.py "$ENCLAVE_ARCH"
