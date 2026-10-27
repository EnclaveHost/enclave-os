#!/bin/sh
# Build a disposable initramfs smoke payload, not a production boot adapter.
set -eu
root=$1
arch=$2
apk add --no-cache cpio
case "$arch" in
    x86_64) kernel=linux-virt ;;
    riscv64) kernel=linux-lts ;;
    *) exit 1 ;;
esac
mkdir -p /tmp/enclave-kernel
apk fetch --no-cache --output /tmp/enclave-kernel "$kernel"
tar -xzf /tmp/enclave-kernel/"$kernel"-*.apk -C /tmp/enclave-kernel
cp /tmp/enclave-kernel/boot/vmlinuz-* /out/smoke-kernel
# Keep this init out of the exported normal userland.
cat > "$root/init" <<'INIT'
#!/bin/sh
set -eu
mount -t proc proc /proc
mount -t sysfs sysfs /sys
sysctl -p /etc/sysctl.d/50-enclave.conf
. /etc/enclave-os/release
test "$NAME" = "Enclave OS"
test "$(cat /proc/sys/kernel/randomize_va_space)" = 2
echo "ENCLAVE_BOOT_OK $(uname -m)"
sync
poweroff -f
INIT
chmod 755 "$root/init"
[ -e "$root/dev/console" ] || mknod -m600 "$root/dev/console" c 5 1
[ -e "$root/dev/null" ] || mknod -m666 "$root/dev/null" c 1 3
(cd "$root" && find . -print0 | cpio --null -o -H newc | gzip -9) >/out/smoke-initramfs.cpio.gz
rm "$root/init" "$root/dev/console" "$root/dev/null"
