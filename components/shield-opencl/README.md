# Musl OpenCL frontend port

These editable sources retain the imported standard OpenCL API frontend,
source/Q8 recognition, authenticated service protocol, lifetime tracking,
fail-closed events and CPU fallback. The import originals and historical Debian
receipts remain under `reference/`; they are not Alpine qualification.

The APK uses a distinct copy of the system CPU ICD loader, LLVM 18 tools at
Alpine's paths and the private patched PoCL package. Its Q8 masked route is
compiled in; capture logging is disabled. Arbitrary source and plaintext never
go to a physical GPU. The installed service and platform policy are still the
security boundary.

The structural IR recognizer is built, but the HIP toolchain and audited reference
bitcode must be rebuilt and installed before IL offload can be qualified. Until
then missing reference data makes IL recognition decline to CPU. That is an open
migration gate, not accepted feature parity. Rejection-hint corpus generation,
full native model tests and actual worker exchanges also remain required.

Package tests cover source semantics, Q8 admission, inherited compiler limits,
rejection-hint keys and program-lifetime races. Separate installed API tests must
exercise the actual CPU ICD and service failures on both architectures.
