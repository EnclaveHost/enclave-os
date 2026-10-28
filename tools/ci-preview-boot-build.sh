#!/bin/sh
set -eux
apk add --no-cache build-base linux-headers python3 cpio cryptsetup
mkdir -p /out/boot-root
apk --root /out/boot-root --initdb --no-cache --keys-dir /etc/apk/keys \
    --repositories-file /etc/apk/repositories add alpine-baselayout busybox cryptsetup
cc -static -O2 -Wall -Wextra -Werror -I/src/components/platform-policy \
    /src/tests/managed-policy-exec.c -o /out/boot-root/policy-exec
cp /src/tests/preview-root-check.py /out/boot-root/root-check.py
cp /src/tests/ffi-policy.py /out/boot-root/ffi-policy.py
python3 - <<'PY'
import json,pathlib,re
p=json.loads(pathlib.Path('/out/kvm-profile.json').read_text())
r=p['root']
assert all(re.fullmatch('[0-9a-f]{64}',r[k]) for k in ('rootHash','salt'))
assert type(r['dataBlocks']) is int and r['dataBlocks']>=2
pathlib.Path('/out/boot-root/verity-env').write_text(
    f"ROOT_HASH={r['rootHash']}\nSALT={r['salt']}\nBLOCKS={r['dataBlocks']}\n")
PY
mkdir -p /out/boot-root/dev /out/boot-root/proc /out/boot-root/sys /out/boot-root/sysroot
cat >/out/boot-root/check <<'CHECK'
#!/bin/sh
set -eux
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
sysctl -w kernel.randomize_va_space=2
. /verity-env
for attempt in 1 2 3 4 5 6 7 8 9 10; do
    [ -b /dev/sda ] && [ -b /dev/sdb ] && break
    sleep 1
done
veritysetup open --no-superblock --format=1 --hash=sha256 \
    --hash-offset=0 --data-block-size=4096 --hash-block-size=4096 \
    --data-blocks="$BLOCKS" --salt="$SALT" /dev/sda preview-root /dev/sdb "$ROOT_HASH"
dd if=/dev/mapper/preview-root of=/dev/null bs=1048576
mount -t squashfs -o ro /dev/mapper/preview-root /sysroot
if touch /sysroot/etc/preview-must-not-write; then exit 1; fi
mount --bind /proc /sysroot/proc
mount --bind /sys /sysroot/sys
mount --bind /dev /sysroot/dev
for directory in run tmp home; do
    mount -t tmpfs -o size=128m tmpfs /sysroot/$directory
done
chmod 1777 /sysroot/tmp
mkdir -p /sysroot/home/desktop /sysroot/dev/shm
chown 1000:1000 /sysroot/home/desktop
chmod 700 /sysroot/home/desktop
mount -t tmpfs -o size=128m,mode=1777 tmpfs /sysroot/dev/shm
cp /policy-exec /root-check.py /ffi-policy.py /sysroot/run/
export HOME=/home/desktop TMPDIR=/tmp POCL_MAX_PTHREAD_COUNT=2 LP_NUM_THREADS=2
chroot /sysroot /run/policy-exec /usr/bin/python3 -I /run/root-check.py
echo ENCLAVE_PREVIEW_ROOT_BOOT_OK
CHECK
cat >/out/boot-root/init <<'INIT'
#!/bin/sh
if ! /bin/sh /check; then echo ENCLAVE_PREVIEW_ROOT_BOOT_FAILED; fi
sync
poweroff -f
INIT
chmod 755 /out/boot-root/init
[ -e /out/boot-root/dev/console ] || mknod -m600 /out/boot-root/dev/console c 5 1
(cd /out/boot-root && find . -print0 | cpio --null -o -H newc | gzip -6) >/out/preview-boot.cpio.gz
rm -rf /out/boot-root
