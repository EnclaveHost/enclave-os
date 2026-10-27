# Verified baseline — 2026-10-27

Source commit: `c8cd28edf9ed9b9c9f53bdcb40cb2b8609feaadf`.

[Both architecture jobs passed](https://github.com/EnclaveHost/enclave-os/actions/runs/40541819527).

| Architecture | Minimal installed bytes | Minimal gzip bytes | Desktop installed bytes | Desktop gzip bytes |
| --- | ---: | ---: | ---: | ---: |
| x86_64 | 8,427,373 | 3,716,473 | 909,118,480 | 332,530,802 |
| riscv64 | 7,149,691 | 3,458,768 | 741,373,103 | 304,293,061 |

Installed bytes count regular file contents; they are not RAM requirements or allocated disk-block usage. Archives contain the userland, without a production kernel, boot firmware, attestation wrapper, models or the still-pending application ports. The desktop baseline includes Firefox ESR, Fluxbox, the custom FreeDoom engine/WAD, audio, noVNC, Python, Node.js, Git and desktop-control tools.

## Checks passed on both architectures

- 705 imported source hashes, deterministic custom source archive checksums and the common feature graph.
- Full-feature assembly refuses to silently omit missing required components.
- Home defaults populate an existing home directory, preserve user changes and preserve private directory permissions.
- All four custom APKs compile, are signed and install through a signed repository with verification enabled.
- The shared Fluxbox session starts with the custom style and browser profile.
- Missing X credentials are rejected; XFixes cursor reads succeed with credentials.
- Cursor singleton enforcement, crash recovery and stalled-process recovery.
- The custom FreeDoom executable starts/renders against Xvfb using the recovered WAD; its completed timedemo exit semantics are accounted for.
- Python, Node.js and Firefox execute inside the assembled architecture-specific root.
- The minimal userland boots with a real Linux kernel under QEMU 11.0.3, reads its Enclave identity, enables ASLR and shuts down cleanly.

The x86-64 runtime checks execute natively. RV64 executable/package tests use QEMU user emulation; the boot check uses QEMU system emulation. These are not the deployed KVM Box admission path or the custom RISC Box emulator.

## Not claimed by this result

This does not qualify the complete desktop boot/device path on either actual Enclave platform, Moonlight audio/input behavior on Alpine, the Enclave Browser fork, Shield compute/graphics, the remaining games, or the measured production root. The `full` preset remains deliberately unavailable until its component ports exist; production qualification remains false for both platform profiles.

The development browser is Alpine Firefox ESR 140.12.0, not Enclave Browser. The maintained Alpine architecture repositories currently have version skew: the tested Node.js binaries report 24.22.1 on x86-64 and 24.18.1 on RV64. Compare the recorded installed-package inventories and rebuild lagging security-sensitive packages against a common supported source baseline before release. Sharing an OS/package definition does not imply every upstream architecture build has the same patch version.

CI artifacts include APKs, the test repository public key, package inventories, per-image size/checksum reports and boot smoke payloads/logs. They expire after seven days and are not a production update feed. Production signing and immutable dependency snapshots remain separate release work.
