#!/bin/sh
set -eux
apk add --no-cache build-base linux-headers python3 cpio nodejs npm ffmpeg
cp /browser-package/*.pub /etc/apk/keys/
printf '\n/browser-package/repository\n' >>/etc/apk/repositories
mkdir -p /out/root /build/tests
apk --root /out/root --initdb --no-cache --keys-dir /etc/apk/keys \
    --repositories-file /etc/apk/repositories add alpine-baselayout busybox musl enclave-browser nodejs font-dejavu
cc -static -O2 -Wall -Wextra -Werror -I/src/components/platform-policy \
    /src/tests/managed-policy-exec.c -o /out/root/policy-exec
cp -a /browser-source/enclave/tests/. /build/tests/
cd /build/tests
npm ci --ignore-scripts --no-audit --no-fund
node media-fixture.mjs
cp -a /build/tests /out/root/tests
cp /src/tests/browser-policy-report.mjs /out/root/tests/
mkdir -p /out/root/proc /out/root/sys /out/root/dev /out/root/tmp
chmod 1777 /out/root/tmp
cat >/out/root/init <<'INIT'
#!/bin/sh
set -eux
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
sysctl -w kernel.randomize_va_space=2
ip link set lo up
export HOME=/tmp TMPDIR=/tmp ENCLAVE_BROWSER_EXECUTABLE=/usr/bin/enclave-firefox
export ENCLAVE_TEST_ARTIFACTS=/tmp/browser-artifacts
if ! /policy-exec /usr/bin/node --jitless /tests/smoke.mjs; then
    echo ENCLAVE_BROWSER_POLICY_FAILED
    sync
    poweroff -f
fi
/usr/bin/node /tests/browser-policy-report.mjs
echo ENCLAVE_BROWSER_POLICY_OK
echo "ENCLAVE_BOOT_OK $(uname -m)"
sync
poweroff -f
INIT
chmod 755 /out/root/init
[ -e /out/root/dev/console ] || mknod -m600 /out/root/dev/console c 5 1
(cd /out/root && find . -print0 | cpio --null -o -H newc | gzip -6) >/out/smoke-initramfs.cpio.gz
