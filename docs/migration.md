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
| Sunshine/Moonlight | Both musl Sunshine builds stream changing encrypted frames to the retained patched x86 Moonlight client | Full native service integration and audio/input parity; real RV64 performance |
| noVNC | Shared Alpine packages | Authenticated platform proxy/socket integration |
| Shield compute | Canonical SDK, exact custom sd.cpp patch and dual-ISA build pipeline | Native SDK/service dual-ISA builds pass; x86 OpenCL, CUDA/HIP and installed IR tests pass; RV64 frontend/HIP and masked worker conformance remain |
| OpenGL/Vulkan | Private musl Mesa package; x86 installed Vulkan/GL compute/draw and wrong-peer rejection pass | Real masked service/worker qualification on both CPUs; never replace Shield routing with direct GPU access |
| OpenArena | Custom ioquake3 input mode bridge | APK rebuilds the recovered engine patch and both native game-module versions; dual-ISA build/startup passed; streamed menu/relative-mode/sensitivity tests remain |
| LibreQuake | QuakeSpasm 0.96.3 + pinned full v0.09-beta campaign APK; shared library dependencies | Dual-ISA musl build/startup passed; real Shield/input/audio qualification remains |
| Visual Pinball X | Pinned engine, retained default table and installed launcher | Core, scripting/spatial audio and image codec build on both CPUs; x86 installed launcher/tables pass; RV64 runtime, plugins and streamed qualification remain |
| OpenHV | Pinned OpenHV/OpenRA shared CIL with native musl libraries | x86 .NET 10 and signed RV64 .NET 12 development runtime startup pass; actual-kernel managed W^X and streamed tests remain |
| Measured root | Existing native SquashFS/verity builder retained | Consume Alpine package root; regenerate measurements, admission and signed catalog artifact |
| RISC boot | Pinned actual emulator, OpenSBI and kernel fixture | Native and Wasm emulator boot Alpine; full desktop/device tests and supported production kernel/admission remain |

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

The corrected [OpenArena baseline](https://github.com/EnclaveHost/enclave-os/actions/runs/40584763752)
passes on both CPUs. [OpenHV on musl .NET 10](https://github.com/EnclaveHost/enclave-os/actions/runs/40588447643)
builds, installs and retains a visible game window through the private graphics
stack. Its NuGet dependency closure is locked. Neither startup fixture establishes
streamed input/audio parity; OpenHV's RV64 runtime remains pending.

The [RV64 Mesa package](https://github.com/EnclaveHost/enclave-os/actions/runs/40591223582)
now builds and installs, with Vulkan/GL capability queries succeeding through the
private stack. [Installed RV64 compute/draw tests](https://github.com/EnclaveHost/enclave-os/actions/runs/40611009310) also pass, including wrong-peer rejection. These use CPU fallback.

The [native SDK](https://github.com/EnclaveHost/enclave-os/actions/runs/40591609962)
builds and installs on both CPUs, including custom llama.cpp/sd.cpp and the Shield
backend. CLI startup does not qualify model numerics or GPU offload.
The [trusted service/core](https://github.com/EnclaveHost/enclave-os/actions/runs/40591960292)
passes both architectures' field reference vectors, half rounding, recovered
compiler/service/Q8 tests, and installed broker/client UID rejection checks.
Actual masked service-to-worker execution and measured adapter admission remain
required.

[Pinball's scripting and spatial-audio dependencies](https://github.com/EnclaveHost/enclave-os/actions/runs/40589801467)
pass on both CPUs, including native VBScript execution. The newer engine requires
its matching FreeImage fork for half-float texture decoding; its package and core
qualification are underway. The RV64 .NET runtime for OpenHV is also undergoing a
separate pinned cross-build; no released runtime or OpenHV RV64 support is claimed.

The [x86 CPU OpenCL package](https://github.com/EnclaveHost/enclave-os/actions/runs/40613687178)
passes actual event semantics, 7,717,008 float-to-half conversions across all four
rounding modes and six vector widths, 393,216 half-tanh evaluations and 78 image
cases. [Installed requalification](https://github.com/EnclaveHost/enclave-os/actions/runs/40614636701)
passes without an external loader-path workaround. Explicit worker stack bounds
fix the musl default-stack overflow; no tests or vector widths were removed.

[Pinball dependencies](https://github.com/EnclaveHost/enclave-os/actions/runs/40610908013)
now include the matching half-float FreeImage fork on both CPUs. The
[x86 core](https://github.com/EnclaveHost/enclave-os/actions/runs/40611425469) and
[rendered-table fixture](https://github.com/EnclaveHost/enclave-os/actions/runs/40614899067)
pass. Both the newer engine's default table and the older engine revision's
example table produce visible 960×600 renderings through private Mesa CPU
fallback. This does not qualify streamed play, audio or plugin parity.

The [Alpine native adapter candidate](https://github.com/EnclaveHost/enclave-os/actions/runs/40614301225)
builds its guarded x86 binaries and passes recovered gateway/automation protocol
tests. [Real-kernel security tests](https://github.com/EnclaveHost/enclave-os/actions/runs/40615018707)
also pass role UID/GID/capability boundaries and confined input-daemon socket and
syscall rules, including inheritance across exec. The exact production kernel
checks remain intact. Complete service startup, input mediation and measured
platform admission are still open.

## Preview and additional qualification, 2026-10-28

The explicit `preview` preset retains every `full` feature and requires all its
packages, including Enclave Browser. It records unfinished qualification rather
than clearing the default full-image release gate. Its separate workflow merges
verified signed package inputs and builds a measured, corruption-tested root.
The result is still not a boot/admission or production deployment claim.

The [actual RISC emulator boot](https://github.com/EnclaveHost/enclave-os/actions/runs/40618669421)
and [Wasm boot](https://github.com/EnclaveHost/enclave-os/actions/runs/40619197984)
reach the pinned Alpine musl userland using the recovered production emulator
implementation. The fixture uses Linux 5.15.164 for compatibility, not an approved
production kernel. It does not yet qualify the full desktop or RV64 isolation.

The [retained Moonlight client](https://github.com/EnclaveHost/enclave-os/actions/runs/40616779298)
builds from its pinned source and recovered patch, and passes audio backlog
boundary tests. [Actual encrypted streaming](https://github.com/EnclaveHost/enclave-os/actions/runs/40622284529)
then pairs that client to the installed musl Sunshine server, validates the server
TLS certificate, requires encrypted transport and observes changing decoded
960×600 frames. This is a disposable CI desktop. Audio continuity, cursor/game
transitions and the full native adapter remain unqualified. No local Moonlight
installation or pairing state was changed.

The [standard llama.cpp/sd.cpp package](https://github.com/EnclaveHost/enclave-os/actions/runs/40616339429)
passes Q8 tensor-view round trips, a mixed CPU/OpenCL graph with 4,096 checked
outputs, and actual device enumeration. The [installed frontend](https://github.com/EnclaveHost/enclave-os/actions/runs/40617930209)
includes the missing Q8 compiler reference files and passes positive/mutated
compiler fixtures. [CUDA/HIP source compatibility](https://github.com/EnclaveHost/enclave-os/actions/runs/40619200767)
passes transpose, vector addition, floating and integer matrix multiplication,
asynchronous calls and pi-scaled math on musl. These executions use CPU fallback.
The [installed audited IR reference](https://github.com/EnclaveHost/enclave-os/actions/runs/40619795731)
passes all nine structural checks, including the actual chipStar wrapper, changed
arithmetic, unknown builtins, global side effects and malformed/specialized SPIR-V.
Recognition alone never grants model/public-weight approval or proves GPU offload.

The [installed Pinball launcher](https://github.com/EnclaveHost/enclave-os/actions/runs/40617171096)
passes both rendered tables and checks the retained writable default-table copy
and 960×600 preferences. Plugins and streamed play remain unqualified.

[RV64 OpenHV startup](https://github.com/EnclaveHost/enclave-os/actions/runs/40617746581)
passes managed arithmetic/threading, SHA-256 and file I/O, then opens the game
through private Mesa. This uses a pinned .NET 12 development runtime, not a
released RV64 .NET 10 runtime. Subsequent APK validation rejected its TEXTREL
markers. The source now requires `-z text` for RV64, and the [rebuilt signed
packages](https://github.com/EnclaveHost/enclave-os/actions/runs/40622790860) install
and pass managed execution and visible OpenHV startup. Actual-kernel managed
W^X tests still remain.

The [native adapter APK](https://github.com/EnclaveHost/enclave-os/actions/runs/40623949487)
now includes static-PIE bootstrap helpers, authenticated web assets with upstream
notices and the recovered public model policies/calibrations. It preserves model
and tensor hashes, peer identities and the fixed masked worker route while using
Alpine package paths. Actual model payload verification and complete startup on
the new root remain required.

The [combined package preflight](https://github.com/EnclaveHost/enclave-os/actions/runs/40624385658)
installs all 293 non-browser dependencies in a clean root and starts the installed
llama.cpp, sd.cpp and HIP command lines. The test includes private proc/sys mounts
and safe character devices; omitting these had prevented musl/hwloc startup in an
earlier harness. This check produces no preview image and does not substitute for
the custom browser build. The [updated composition](https://github.com/EnclaveHost/enclave-os/actions/runs/40625672606)
also passes with the current native and desktop APKs. It exercises native root
preparation, keeps the single input rule set, starts with empty session mounts,
retains the browser extension and merges the fixed SOCKS policy, then verifies
the recovered model-policy/calibration bindings.

The [updated shared desktop](https://github.com/EnclaveHost/enclave-os/actions/runs/40625428557)
passes authenticated X, visible cursor, singleton and crash/hang recovery tests
on both CPUs. It retains the signed uBlock Origin 1.75.0 XPI from the recovered
image; actual extension loading in the new browser remains part of browser
integration qualification.

The [clean-source KVM kernel fixture](https://github.com/EnclaveHost/enclave-os/actions/runs/40621991327)
retains the exact `6.6.87.2-enclave-kvm-box` ABI and recovered OpenHCL TPM driver.
[Actual policy tests on that kernel](https://github.com/EnclaveHost/enclave-os/actions/runs/40624681299)
pass W^X refusal, inherited seccomp and role/input-daemon confinement under TCG.
This does not establish a full native service graph, hardware attestation,
production admission or a kernel security-update qualification.

The [RV64 encrypted stream](https://github.com/EnclaveHost/enclave-os/actions/runs/40632814126)
also passes using the installed RV64 Sunshine APK and retained x86 Moonlight
client. It confirms decoded changing 960×600 frames with verified TLS and required
encrypted transport under user emulation, not real RV64 frame rate or audio/input
parity. The [RV64 Pinball core](https://github.com/EnclaveHost/enclave-os/actions/runs/40615372405)
builds, but the first installed runtime test could not identify a visible player
window after initialization; that runtime gate remains open.

The [RV64 installed CPU OpenCL checks](https://github.com/EnclaveHost/enclave-os/actions/runs/40633505873)
pass all 7,717,008 half conversions, 393,216 half-tanh evaluations and 78 image
read/write cases. Selecting a baseline RV64GC CPU when LLVM reports generic-rv64
fixes the missing floating-point helper failure. The cold image test took 185
seconds under emulation, exceeding the original 180-second fixture limit; it
passes with the complete unchanged case set and a bounded emulation allowance.

The [KVM boot-input composition check](https://github.com/EnclaveHost/enclave-os/actions/runs/40633804435)
passes with the existing launcher's fixed helper paths and the pinned kernel's
`nft_ct.ko`. Regular hard links preserve no-symlink boot checks and share the APK's
helper bytes. The separate preview will export the kernel and static helpers for
platform archive construction; this is not a complete boot/admission result.
