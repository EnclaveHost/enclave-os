#!/bin/sh
set -eux
apk add --no-cache build-base linux-headers python3 cpio
mkdir -p /out/root
cc -static -O2 -Wall -Wextra -Werror /src/components/platform-policy/test-policy.c -o /out/root/policy-test
if [ "$ENCLAVE_ARCH" = x86_64 ]; then
    cc -static -O2 -Wall -Wextra -Werror -I/src/components/platform-policy \
        /src/components/native-platform/test-roles.c -o /out/root/native-roles-test
fi
apk --root /out/root --initdb --no-cache --keys-dir /etc/apk/keys --repositories-file /etc/apk/repositories add busybox musl
mkdir -p /out/root/etc/enclave-os /out/root/etc/sysctl.d /out/root/proc /out/root/sys /out/root/dev
printf 'NAME="Enclave OS"\n' >/out/root/etc/enclave-os/release
printf 'kernel.randomize_va_space=2\n' >/out/root/etc/sysctl.d/50-enclave.conf
ENCLAVE_POLICY_TEST=1 /bin/sh /src/tools/boot-payload.sh /out/root "$ENCLAVE_ARCH"
