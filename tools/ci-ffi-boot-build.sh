#!/bin/sh
set -eux
mkdir -p /out/root
apk --root /out/root --initdb --no-cache --keys-dir /etc/apk/keys \
    --repositories-file /etc/apk/repositories add alpine-baselayout busybox python3 \
    /out/repository/riscv64/libffi-[0-9]*.apk
cp /out/policy-exec /out/root/policy-exec
cp /src/tests/ffi-policy.py /out/root/ffi-policy.py
mkdir -p /out/root/proc /out/root/sys /out/root/dev /out/root/tmp
cat >/out/root/init <<'INIT'
#!/bin/sh
set -eux
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mount -t tmpfs -o size=32m,mode=1777,noexec,nosuid,nodev tmpfs /tmp
export HOME=/tmp TMPDIR=/tmp
sysctl -w kernel.randomize_va_space=2
/policy-exec /usr/bin/python3 -I /ffi-policy.py
echo ENCLAVE_FFI_POLICY_OK
echo "ENCLAVE_BOOT_OK $(uname -m)"
sync
poweroff -f
INIT
chmod 755 /out/root/init
[ -e /out/root/dev/console ] || mknod -m600 /out/root/dev/console c 5 1
(cd /out/root && find . -print0 | cpio --null -o -H newc | gzip -6) >/out/smoke-initramfs.cpio.gz
rm -rf /out/root
