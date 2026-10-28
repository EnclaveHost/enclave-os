#!/bin/bash
set -euo pipefail
mkdir -p out
curl -fLSs https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.15.164.tar.xz -o out/linux.tar.xz
printf '%s\n' 'ec6098faed64b8a47ba1772e812a6eb444385f7aa3c60d3e4739ab2fd3b29186  out/linux.tar.xz' | sha256sum -c -
tar -xf out/linux.tar.xz -C out
kernel="$PWD/out/linux-5.15.164"
make -C "$kernel" ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- defconfig
"$kernel/scripts/kconfig/merge_config.sh" -m -O "$kernel" "$kernel/.config" reference/risc-box/guest/kernel.fragment
"$kernel/scripts/config" --file "$kernel/.config" -e SECCOMP -e SECCOMP_FILTER -e EXT2_FS -d WERROR -d DEBUG_INFO
make -C "$kernel" ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- olddefconfig
make -C "$kernel" ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- -j2 Image >out/kernel-build.log 2>&1
make -C opensbi CROSS_COMPILE=riscv64-linux-gnu- PLATFORM=generic \
    PLATFORM_RISCV_ISA=rv64imafdc_zicsr_zifencei FW_PIC=n \
    FW_PAYLOAD_PATH="$kernel/arch/riscv/boot/Image" -j2 >out/firmware-build.log 2>&1
cp opensbi/build/platform/generic/firmware/fw_payload.elf out/
cp "$kernel/.config" out/kernel.config
python3 - <<'PY'
import hashlib,json,pathlib,urllib.request
lock=json.loads(pathlib.Path('profiles/upstream-lock.json').read_text())
url=f'https://dl-cdn.alpinelinux.org/alpine/{lock["alpine_branch"]}/releases/riscv64/alpine-minirootfs-{lock["alpine_version"]}-riscv64.tar.gz'
data=urllib.request.urlopen(url).read()
assert hashlib.sha256(data).hexdigest()==lock['minirootfs']['riscv64']['sha256']
pathlib.Path('out/rootfs.tar.gz').write_bytes(data)
PY
mkdir out/root
sudo tar -xf out/rootfs.tar.gz -C out/root
sudo mkdir -p out/root/proc out/root/sys out/root/dev
sudo mknod -m600 out/root/dev/console c 5 1
sudo tee out/root/enclave-smoke >/dev/null <<'INIT'
#!/bin/sh
set -eu
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
test "$(uname -m)" = riscv64
test -x /lib/ld-musl-riscv64.so.1
/bin/busybox sha256sum /etc/alpine-release
/lib/ld-musl-riscv64.so.1 --list /bin/busybox
echo ENCLAVE_RISC_ALPINE_BOOT_OK
while :; do sleep 100; done
INIT
sudo chmod 755 out/root/enclave-smoke
printf '%s\n' '::sysinit:/enclave-smoke' | sudo tee out/root/etc/inittab >/dev/null
truncate -s 96M out/rootfs.ext2
sudo mke2fs -q -t ext2 -d out/root out/rootfs.ext2
sudo chown "$(id -u):$(id -g)" out/rootfs.ext2
