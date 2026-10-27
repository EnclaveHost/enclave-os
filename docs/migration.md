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
| Sunshine/Moonlight | Pinned source-based X11/software-encoder APK in progress for both CPUs; client audio/input patch preserved in `integrations/moonlight` | Finish musl builds, RV64 capture/encoder feasibility; authenticated service integration and audio/input parity |
| noVNC | Shared Alpine packages | Authenticated platform proxy/socket integration |
| Shield compute | Canonical SDK, exact custom sd.cpp patch and dual-ISA build pipeline | Rebuild native dependencies for musl and each ISA; masked operation and CPU fallback conformance |
| OpenGL/Vulkan | Private musl Mesa package; x86 installed Vulkan/GL compute/draw and wrong-peer rejection pass | Finish RV64 build and real masked service/worker qualification; never replace Shield routing with direct GPU access |
| OpenArena | Custom ioquake3 input mode bridge | APK rebuilds the recovered engine patch and both native game-module versions; dual-ISA build, menu/relative-mode/sensitivity tests remain |
| LibreQuake | QuakeSpasm 0.96.3 + pinned full v0.09-beta campaign APK; shared library dependencies | Dual-ISA musl build/startup passed; real Shield/input/audio qualification remains |
| Visual Pinball X | Imported runtime inventory | Engine/dependency portability, table distribution/licensing, graphics qualification |
| OpenHV | Pinned OpenHV/OpenRA source port to shared .NET 10 and native musl libraries | x86 build/startup, RV64 runtime port, W^X and rendering tests |
| Measured root | Existing native SquashFS/verity builder retained | Consume Alpine package root; regenerate measurements, admission and signed catalog artifact |
| RISC boot | Existing OpenSBI/Buildroot/kernel sources retained | Reconcile newer musl/Xorg requirements with emulator ISA and kernel; rebuild payload and disk |

There is **one** shared OS definition; platform profiles only select architecture, display driver and boot boundary. Features unavailable on one architecture remain explicitly pending. They must not silently disappear from a release advertised as equivalent.

## Security contract

The desktop is unprivileged. Platform startup creates fresh session credentials and authenticated X sockets; no credential is baked into the rootfs. Only the masked Shield service may reach GPU compute; desktop software must not receive raw DRM/CUDA or host GPU passthrough. Unsupported work stays on the CPU.

W^X enforcement belongs in the platform boundary, with forbidden allocation requests rejected rather than killing the entire VM. The imported native seccomp code is **x86-64-specific**. Its editable port in `components/platform-policy` uses native libc syscall constants and separate x86-64/RV64 architecture guards; the dedicated kernel tests and actual adapter admission remain required before use. Browser preferences are defense in depth, not a substitute for that enforcement.

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
on both musl architectures with undefined-behavior checks (diagnostics on x86-64,
traps on RV64 where Alpine does not ship libubsan). Its synthetic replies are not evidence of
GPU execution, and the actual Mesa/service/worker chain remains a release gate.

The [native ABI policy run](https://github.com/EnclaveHost/enclave-os/actions/runs/40585361714)
passes under actual x86-64 and RV64 Linux kernels. It checks denied RWX requests,
legal RW-to-RX transitions, inherited restrictions and fatal forbidden syscalls.
This does not establish production adapter admission.

The [installed graphics API run](https://github.com/EnclaveHost/enclave-os/actions/runs/40587616031)
passes x86 musl Vulkan compute-to-draw, OpenGL compute, robust-context creation and
rejection of a compute socket owned by the wrong UID before any request is sent.
These are real API executions through the installed private Mesa APK, using CPU
fallback; they are not claims of GPU offload.

Enclave Browser's [nine-check native qualification](https://github.com/EnclaveHost/enclave-browser/actions/runs/40585509254)
passes Fission navigation, focused keyboard input, interception, downloads, cookies,
TLS/CSP denial and 960×600 VP9 playback. The native binary provenance is retained
by that workflow; this JS qualification does not replace the musl/RV64 build gates.
