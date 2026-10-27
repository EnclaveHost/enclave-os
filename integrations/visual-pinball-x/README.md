# Visual Pinball portability work

The deployed 10.8.0-2052 engine uses a prebuilt BASS library unavailable for the
shared musl/RV64 target. It is not repackaged as a portable binary. Upstream
removed BASS in commit aefd9558aa1c3aae0d39c1bf3c86ad336873c07d. A newer candidate,
099c8a3864683582a2f89403c14525edcb7c4f02, supports system libraries and separates
VBScript and spatial audio into portable libraries. Its exact dependency pins
are used by the two APK recipes here.

`pinball-deps.yml` builds both CPUs and verifies actual VBScript expression,
loop/string and host-callback execution. This is dependency qualification, not
an installed game or proof of preserved gameplay/audio. The engine, plugins,
retained tables and desktop launcher still need packaging and testing. Keep the
full profile gated until these pass; do not substitute this work for the running
VPX installation. Table and engine upgrade compatibility must be demonstrated.

The RV64 libwinevbs header port selects 64-bit COM interfaces and provides opaque
pointer declarations for unused Windows exception types. It does not invent a
Windows RISC-V register layout or implement native Windows code/SEH. Runtime
interpreter checks are required on both CPUs.

`vpx-core.yml` builds the pinned newer engine candidate against shared SDL3,
FreeImage, hidapi and the scripting/audio APKs. `enclave-vpx-core` is deliberately
a component package without the public game launcher: plugins, retained-table
compatibility, streamed controls and audio remain required before promotion.
Both CPUs use desktop OpenGL through Shield; RV64 is not implicitly switched to
a reduced GLES feature set.
