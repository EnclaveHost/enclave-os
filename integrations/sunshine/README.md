# Streaming server migration

The existing VM imports upstream Sunshine 2026.914.233613 and Enclave runtime
configuration. The recovered custom input/audio changes are in the Moonlight
client (`../moonlight`); no modified Sunshine engine source was recovered.

The portable recipe pins Sunshine commit
`63d35f702ee9e362e43263742981836ec0710384` and all recursive submodules. It rebuilds
the matching FFmpeg/CBS sources with x264/x265, adds RV64 to CBS's architecture
selection, and compiles X11 capture with software encoding. CUDA, DRM, VAAPI,
Vulkan encoding and compositor capture backends are disabled. This retains the
existing VM's X11/software streaming path and does not grant host GPU access.

CI archives the Git/submodule provenance and generated APK source checksum. The
package does not install host udev permissions or a system-wide service. The
platform adapter must supply authenticated X, the input broker, PulseAudio and
per-user pairing state, with mandatory encrypted streaming and loopback binding
from the recovered configuration. Never bake credentials or pairing keys into an
image. Build/version checks alone do not qualify pairing, cursor or sound parity.
