#!/bin/sh
# Disposable Alpine container only; never run on a production VM.
set -eux
apk add --no-cache alpine-sdk sudo python3 libx11-dev libxfixes-dev xvfb xauth
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave /out
python3 /src/tools/stage-aports.py /home/builder/aports/enclave
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
for name in base cursor desktop freedoom; do
    su builder -c "cd /home/builder/aports/enclave/enclave-$name && abuild -r"
    if [ "$name" = base ]; then
        printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
    fi
    apk update
done
mkdir -p /out/repository
cp -a /home/builder/packages/enclave/. /out/repository/
cp /home/builder/.abuild/*.pub /out/
# No private signing material leaves this disposable builder.
apk add --no-cache enclave-base enclave-cursor enclave-desktop enclave-freedoom
cc /src/tests/cursor-image.c -o /tmp/cursor-image -lX11 -lXfixes
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix
su builder -c 'python3 /src/tests/desktop-smoke.py'
for preset in minimal desktop; do
    python3 /src/tools/assemble.py --arch "$ENCLAVE_ARCH" --preset "$preset" \
        --repository /out/repository --key /out/*.pub --output "/out/root-$preset"
    chroot "/out/root-$preset" /bin/busybox true
    chroot "/out/root-$preset" /bin/sh -c 'test "$(cat /etc/alpine-release)" = 3.24.3'
    if [ "$preset" = desktop ]; then
        chroot /out/root-desktop /usr/bin/python3 --version
        chroot /out/root-desktop /usr/bin/node --version
        # Firefox resolves its executable through procfs, as in a booted OS.
        mount -t proc proc /out/root-desktop/proc
        trap 'umount /out/root-desktop/proc || true' EXIT
        chroot /out/root-desktop /usr/bin/firefox-esr --version
        umount /out/root-desktop/proc
        trap - EXIT
    fi
    if [ "$preset" = minimal ]; then
        /src/tools/boot-payload.sh "/out/root-$preset" "$ENCLAVE_ARCH"
    fi
    tar -cf "/out/enclave-os-$ENCLAVE_ARCH-$preset-rootfs.tar" -C "/out/root-$preset" .
    rm -rf "/out/root-$preset"
done

