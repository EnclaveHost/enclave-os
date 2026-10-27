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
