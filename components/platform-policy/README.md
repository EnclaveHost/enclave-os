# Architecture-specific desktop policy

This is the editable Enclave OS port of the imported native runtime policy.
`reference/` retains the original x86-64 source and provenance unchanged.
The base denials are preserved, but syscall numbers come from the target libc.
Only little-endian x86-64 and RV64 builds are accepted. x32 is rejected on x86-64.
The resulting BPF measurement is specific to the architecture and must enter
that platform's admission manifest.

The memory refinement rejects simultaneous writable/executable requests with
EPERM so a failed allocation does not kill the desktop. RW-to-RX transitions
remain possible. This filter does not detect executable ELF segments or aliases
of the same backing memory; retain the platform's measured-file admission and
mapping attestation. It is not a complete W^X proof on its own.

The caller must drop privileges, set no-new-privileges, and install the filter
in each single-threaded runtime child before exec, refusing launch on failure.
Do not install this filter on the trusted front/service roles.

The separate security workflow compiles a static musl probe for both ISAs and
boots each in a real emulated Linux kernel. It checks denied RWX requests while
preserving the existing mapping, legal RW/RX transitions, SHM/personality paths,
restricted interfaces, child inheritance and mandatory SIGSYS denials. A
successful test is a kernel/ABI gate, not evidence that the production adapters
already install this new measured policy.
