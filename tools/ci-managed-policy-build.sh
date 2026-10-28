#!/bin/sh
set -eux
apk add --no-cache build-base linux-headers python3 cpio
mkdir -p /out/root
if [ "$ENCLAVE_ARCH" = riscv64 ]; then
    cp /packages/*.pub /etc/apk/keys/
    printf '\n/packages/repository\n' >>/etc/apk/repositories
    runtime=enclave-dotnet-riscv
else
    runtime=dotnet10-runtime
fi
apk --root /out/root --initdb --no-cache --keys-dir /etc/apk/keys \
    --repositories-file /etc/apk/repositories add alpine-baselayout busybox musl "$runtime"
cc -static -O2 -Wall -Wextra -Werror -I/src/components/platform-policy \
    /src/tests/managed-policy-exec.c -o /out/root/policy-exec
mkdir -p /out/root/managed /out/root/proc /out/root/sys /out/root/dev /out/root/tmp
chmod 1777 /out/root/tmp
cp /managed/* /out/root/managed/
cat >/out/root/init <<'INIT'
#!/bin/sh
set -eux
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
export HOME=/tmp TMPDIR=/tmp DOTNET_EnableWriteXorExecute=1 COMPlus_EnableWriteXorExecute=1
export DOTNET_EnableDiagnostics=0 COMPlus_LTTng=0 DOTNET_ReadyToRun=0 COMPlus_ReadyToRun=0
export DOTNET_PROCESSOR_COUNT=2 ENCLAVE_EXPECT_POLICY=1
sysctl -w kernel.randomize_va_space=2
test "$(cat /proc/sys/kernel/randomize_va_space)" = 2
case "$(uname -m)" in
    riscv64) set -- /usr/lib/enclave-dotnet/dotnet exec --fx-version 12.0.0-dev ;;
    x86_64) set -- /usr/bin/dotnet exec ;;
    *) exit 1 ;;
esac
/policy-exec "$@" /managed/managed-runtime.dll "$(uname -m)"
echo "ENCLAVE_BOOT_OK $(uname -m)"
sync
poweroff -f
INIT
chmod 755 /out/root/init
[ -e /out/root/dev/console ] || mknod -m600 /out/root/dev/console c 5 1
(cd /out/root && find . -print0 | cpio --null -o -H newc | gzip -6) >/out/smoke-initramfs.cpio.gz
