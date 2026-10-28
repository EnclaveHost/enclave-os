# Enclave OS

One lightweight Alpine Linux userland for **RISC Box (riscv64)** and **KVM Box Native (x86_64)**. The desktop, package recipes, configuration and security requirements are shared. Firmware, kernel, display devices and the measured startup boundary belong to platform adapters.

This is the home for the VM customizations previously embedded in `EnclaveHost/enclave-apps`. It is a development distribution, **not yet a replacement for the deployed, attested KVM image**. CI builds real APKs and assembles both architectures; boot integration, Shield qualification and application ports remain release gates.

The explicit `preview` preset requests the same features as `full` while recording
the unfinished qualification gates in its inventory. It exists for the requested
separate KVM Box Native trial; it never substitutes stock Firefox or removes a
missing game to complete assembly. `preview.yml` consumes identified successful
x86 package jobs, verifies APK signatures, assembles the root and corruption-tests
its dm-verity sidecar. That artifact still needs native adapter startup/admission
before it can be offered as a running preview. The default `full` preset remains
blocked until the migration matrix passes, and no workflow replaces production.

## Verified footprint

[The dual-architecture build and boot checks pass](https://github.com/EnclaveHost/enclave-os/actions/runs/40541819527). These are development userlands; full platform/feature parity remains work in progress.

| Architecture | Minimal base, gzip | Desktop baseline, gzip |
| --- | ---: | ---: |
| x86-64 | 3.54 MiB | 317.13 MiB |
| RISC-V 64 | 3.30 MiB | 290.20 MiB |

These historical desktop figures include stock Firefox, custom FreeDoom, audio, noVNC, Python and Node.js. They exclude the pending Shield/streaming/game ports and production boot wrapper. See [exact sizes, checks and limitations](docs/validation-20261027.md).

## Why Alpine, and why was the native image Debian?

Alpine was selected for the RISC desktop's small footprint. The native port used Debian 13 to reuse its Firefox ESR and a prebuilt Sunshine `.deb`. KVM does not require Debian. Maintaining separate application and desktop stacks would accumulate drift, so Alpine/musl is the common base here.

The migration keeps the useful RISC optimizations: a tiny GTK theme, Fluxbox, 960×600, small browser process/cache budgets, and the custom FreeDoom renderer and music implementation. It also keeps the native fixes: authenticated X, the persistent cursor owner, outline window dragging and W^X-aware browser defaults. Historical RISC settings that disabled ASLR, certificate checks or Safe Browsing are **not** installed by the new packages.

## Lightweight without removing features

- The default image target is `full`, including all four custom games and FreeDoom on both CPUs. It refuses assembly while any required port is missing; it cannot silently ship a reduced replacement. `minimal` and `desktop` are explicitly selected development subsets, not the shared release image.
- Browser and games start on demand. There is no permanently warmed Firefox, second browser or desktop compositor.
- Packages use native musl binaries and shared libraries. Build tools and source trees stay in the builder; `abuild` strips installed binaries. No Debian compatibility root or duplicated glibc runtime is installed.
- The complete desktop keeps the existing 960×600 resolution and browser 30 FPS setting. This migration does not lower stream quality, remove accessibility, disable web animations or break certificate verification to save CPU.
- Larger games, Moonlight and Shield are separate components with explicit port status. Their separation permits small images; it is **not** a decision to remove them from the final full desktop.
- The existing x86 desktop includes custom **OpenArena, LibreQuake, Visual Pinball X and OpenHV** installations. All four are required in the replacement full image, alongside FreeDoom. Preserve their game content, launchers, input/cursor settings, audio fixes and Shield routing; substituting stock packages alone does not establish parity. “Pending” means their Alpine ports are unfinished, not that the games are absent from the existing desktop.
- Image artifacts include an installed-package database and measured byte count. Size claims are based on these reports, not the size of the bootstrap download.

## Build and validation

The [build workflow](https://github.com/EnclaveHost/enclave-os/actions/workflows/build.yml) uses a digest-pinned Alpine 3.24.3 builder for x86-64 and RISC-V. RISC-V uses QEMU user-mode emulation for compilation and executable tests.

```sh
# Validate references, security defaults, shared profiles and source checksums.
python3 tests/contracts.py

# Stage deterministic source archives beside the APKBUILD recipes.
python3 tools/stage-aports.py staging
```

The disposable CI builder compiles six packages, signs a temporary APK repository, installs it with signature verification, checks X authentication and cursor recovery, and starts the custom FreeDoom engine. It also compiles QuakeSpasm against musl, packages the pinned full LibreQuake campaign and runs an isolated CPU-rendered startup check. OpenArena also rebuilds the recovered input patch and native game modules, retaining the pinned full assets. These startup tests do not qualify Shield rendering or streaming. It then assembles minimal and browser-free shell development root filesystems, executes their native programs, boots the minimal OS with real Linux kernels under system emulation, and exports rootfs archives, package inventory, size reports and checksums. Compression runs on the native CI host to avoid wasting time emulating gzip. See `tools/ci-build.sh` for the exact commands.

**Do not run `ci-build.sh` on a workstation or running guest**: it provisions a disposable Alpine build container. The workflow shows the container invocation. CI public keys are test-only; no private key is published and test keys are removed from final rootfs trust stores. Development artifacts are not production releases and do not automatically update running apps.

## Repository map

| Path | Purpose |
| --- | --- |
| `components/` | Canonical portable cursor, desktop, base policy and custom fbDOOM sources |
| `aports/` | APK package recipes and source checksums |
| `profiles/` | Shared feature graph, per-architecture device selection and bootstrap pins |
| `platforms/` | Display adapters; platform boot/security integration contract |
| `tools/` | Reproducible source staging and clean-root assembly |
| `integrations/` | Recovered OpenArena and Moonlight patches with pinned upstream provenance |
| `provenance/` | Imported source hashes, upstream availability snapshot and runtime customization inventory |
| `reference/` | Frozen original RISC/native build inputs, Shield sources and historical documentation |
| `docs/` | Migration matrix, release gates and packaging policy |

`reference/` is an audit/migration source, not an overlay to copy into an image. Its old deployment claims and weaker RISC defaults are historical. One developer SSH authorized key was deliberately excluded. No user credentials, wallet material, live browser profile or private signing keys are imported.

## Release scope

The initial APKs are `enclave-base`, `enclave-cursor`, `enclave-desktop` and `enclave-freedoom`. The native C components are rebuilt against musl for both architectures. Both `desktop` and `full` select the custom [`enclave-browser` APK](https://github.com/EnclaveHost/enclave-browser/tree/enclave-esr153/enclave/alpine), built from Enclave Browser's engine fork. The desktop launcher requires `enclave-firefox` and never falls back to stock Firefox. Its musl build and browser qualification are in progress; a signed browser APK must be supplied before assembling either preset. The explicit `shell` preset is the browser-free development test image, not a replacement desktop.

The [migration matrix](docs/migration.md) records Sunshine, Enclave Browser, Shield compute/graphics and game work that must be completed before claiming parity with the running native VM. User-mode tests are not proof that the RISC Box emulator can boot this newer userland/kernel combination or that KVM admission/attestation accepts it. Those are separate mandatory release checks.

## Licensing

Original Enclave code retains the [Enclave Source-Available License](LICENSE). Publishing the source does not make that code open source. Third-party components retain their own licenses, including fbDOOM, Nuked OPL3, FreeDoom, Alpine packages, Mesa and the referenced browser sources. Preserve their notices and corresponding-source obligations when producing releases.
