# Platform adapters

Both adapters consume the same profile and APK-built userland. They supply kernel/firmware, devices, root integrity, writable mounts, networking, identities, X authentication and service supervision.

- **kvm-box:** measured x86-64 kernel, existing isolated startup/UID boundaries, readonly root, dummy X display. Port the retained native builder from Debian paths to the Alpine root and qualify W^X/seccomp and masked GPU routing before publishing an image.
- **risc-box:** OpenSBI + kernel payload, virtio disk and simplefb display. Retain the old build sources as reference, but validate the emulator ISA/kernel against Alpine 3.24. Its old root-owned X desktop is not the new security contract.

The Xorg snippets preserve 960×600. They are not complete boot configurations. `enclave-desktop-session` is invoked only as the desktop user after the adapter has started authenticated X. The session does not start networking, enable SSH, manufacture passwords or grant device access.

The image assembler deliberately emits a userland rootfs, not a purportedly attested boot disk. Add adapter packaging only when its actual boot and security tests pass.
