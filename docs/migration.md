# Reconciliation and release gates

The source import is pinned in `provenance/import.json`, including hashes and an explicit marker for uncommitted cursor candidates. Other dirty files in the source checkout were imported from the recorded Git commit, so unrelated work was not incorporated. The current deployed system was identified as Debian 13.7; its public game launchers are in `provenance/runtime-inventory.json`.

The user confirmed on 2026-10-27 that the x86 image includes custom OpenArena, LibreQuake, Visual Pinball X and OpenHV installations. These are existing features to retain, not optional additions. All four already appear in the required `full` preset. Their pending status describes the Alpine migration only; the smaller measured `desktop` baseline excludes them and must not be presented as the complete replacement image.

For each game, recover and pin the installed engine/content versions, custom source changes, launcher and configuration before packaging. The captured launcher inventory is not a complete backup of binaries, game assets or user settings. OpenArena's recovered source patch is in `integrations/openarena`; do not infer equivalent source recovery or working Alpine ports for the other games from the launcher inventory. Validate menu clicks, gameplay input and per-game sensitivity, non-inverted aiming where applicable, cursor restoration after exit, audio and Shield graphics routing. Visual Pinball X replaces Neverball in the retained game selection.

| Component | Common implementation | Remaining qualification |
| --- | --- | --- |
| OS/libc/package manager | Alpine 3.24 / musl / APK for both CPUs | Boot on each real platform; syscall/kernel compatibility |
| Desktop | Fluxbox, tiny theme, 960×600, outline dragging | Real input, clipboard, resize and accessibility checks |
| Cursor | Persistent X cursor owner and supervised recovery, authenticated X | Moonlight desktop/game transitions on both adapters |
| FreeDoom | Same recovered Phase 1 WAD, custom renderer and native OPL code, musl rebuild | Audio latency/quality and sustained gameplay on real targets |
| Browser | Custom Enclave Browser APK selected by desktop/full; stock fallback removed | Enclave Browser musl/RV64 builds, browser security gates, Playwright/Fission tests, video playback |
| Sunshine/Moonlight | Alpine x86-64 upstream APK exists; client audio/input patch preserved in `integrations/moonlight` | Build/verify patched Sunshine on musl, RV64 capture/encoder feasibility; audio/input parity |
| noVNC | Shared Alpine packages | Authenticated platform proxy/socket integration |
| Shield compute | Imported worker/protocol/SDK source | Rebuild native dependencies for musl and each ISA; masked operation and CPU fallback conformance |
| OpenGL/Vulkan | Imported patched Mesa/driver source | Musl toolchain, platform ISA, full qualification suite; never replace Shield routing with direct GPU access |
| OpenArena | Custom ioquake3 input mode bridge | APK rebuilds the recovered engine patch and both native game-module versions; dual-ISA build, menu/relative-mode/sensitivity tests remain |
| LibreQuake | QuakeSpasm 0.96.3 + pinned full v0.09-beta campaign APK; shared library dependencies | Dual-ISA musl build/startup and real Shield/input/audio qualification |
| Visual Pinball X | Imported runtime inventory | Engine/dependency portability, table distribution/licensing, graphics qualification |
| OpenHV | OpenRA/.NET 6 game + content | Supported musl runtime/architecture, shared runtime packaging, W^X and rendering tests |
| Measured root | Existing native SquashFS/verity builder retained | Consume Alpine package root; regenerate measurements, admission and signed catalog artifact |
| RISC boot | Existing OpenSBI/Buildroot/kernel sources retained | Reconcile newer musl/Xorg requirements with emulator ISA and kernel; rebuild payload and disk |

There is **one** shared OS definition; platform profiles only select architecture, display driver and boot boundary. Features unavailable on one architecture remain explicitly pending. They must not silently disappear from a release advertised as equivalent.

## Security contract

The desktop is unprivileged. Platform startup creates fresh session credentials and authenticated X sockets; no credential is baked into the rootfs. Only the masked Shield service may reach GPU compute; desktop software must not receive raw DRM/CUDA or host GPU passthrough. Unsupported work stays on the CPU.

W^X enforcement belongs in the platform boundary, with forbidden allocation requests rejected rather than killing the entire VM. The existing native seccomp code is **x86-64-specific** and must not be reused on RV64 without a separately tested syscall-ABI implementation. Browser preferences are defense in depth, not a substitute for that enforcement.

ASLR, TLS/certificate validation, Safe Browsing and site isolation remain enabled. Xorg SECURITY must remain enabled. The new desktop session refuses to start without a readable authority file and inherits the adapter's display/authority rather than assuming Debian paths.

## Deployment gate

1. Both architecture APK builds and signed install tests pass.
2. Both full userlands boot on the actual RISC Box and KVM Box launch paths.
3. The native isolation boundary and the RV64 boundary pass their respective security tests.
4. The retained app matrix passes input/cursor, graphics, sound, browser video and agent tests; unsupported features are reported honestly.
5. Produce immutable roots, package/SBOM inventories, verified provenance and new platform measurements.
6. Publish signed releases and catalog updates through the normal deployment path. Never overwrite the known-good deployed Debian image while migration gates are open.

## Source references

- [Alpine release policy](https://alpinelinux.org/releases/)
- [Alpine x86-64 release manifests](https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/x86_64/)
- [Alpine RISC-V release manifests](https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/riscv64/)
- [Sunshine release with Alpine packages](https://github.com/LizardByte/Sunshine/releases/tag/v2026.914.233613)
- [Alpine package creation](https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package)

## Migration evidence, 2026-10-27

Run [40579464934](https://github.com/EnclaveHost/enclave-os/actions/runs/40579464934)
built and installed the LibreQuake APK, started its native musl engine with the full
campaign, and passed the minimal Linux boot checks on x86-64 and RV64. The game
startup fixture uses CPU rendering and dummy audio; it does not establish streamed
input/audio or masked graphics parity. The browser-free `shell` artifact is an
explicit development fixture. `desktop` and `full` require the custom Enclave
Browser package and cannot substitute Alpine Firefox.

The canonical graphics client and NIR proof sources now live in
`components/shield-graphics`; `reference/` retains the imported originals. The
separate Shield workflow checks the exact integer transport and rejection behavior
on both musl architectures with UBSan. Its synthetic replies are not evidence of
GPU execution, and the actual Mesa/service/worker chain remains a release gate.
