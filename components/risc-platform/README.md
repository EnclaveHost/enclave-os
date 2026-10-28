# RISC Box Alpine boot qualification

The vendored emulator is the exact recorded RISC Box revision, including its
custom CPU, compressed disk, framebuffer, input and audio devices. `source.json`
records every imported source digest. The runner uses that implementation to boot
a fresh Alpine 3.24 musl filesystem; it does not substitute QEMU for RISC Box.
The same runner also compiles to Wasm. The separate `risc-wasm-boot.yml` job
executes that exact artifact with a hash-pinned Wasmtime and only its fixture
directory exposed. Native boot, Wasm boot and production adapter admission remain
distinct gates.

The disposable boot fixture retains the known-compatible Linux 5.15.164/OpenSBI
0.9 combination to expose userland/ISA incompatibilities independently of a
kernel upgrade. These are test inputs, not an approved production kernel. A
supported kernel update, W^X boundary, authenticated unprivileged desktop, masked
service routing, full root and production Wasm adapter boot are still required.
No previous root, snapshot, pairing key or user credential enters the fixture.
