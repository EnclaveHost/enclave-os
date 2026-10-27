# Trusted compute service port

The editable service, graph compiler, Q8 broker and regression tests are recovered
from `reference/kvm-box/shield-compute`. The package builds the non-dealer masking
core at Enclave commit `04a27e8da4e7d8a5f4b1270e6d02231a2b96d29a`, retaining
field arithmetic, mask generation and verification. RV64 uses the existing scalar
implementation; x86 retains runtime SIMD dispatch. Both preserve PIC, Alpine C
hardening and `-ffp-contract=off` for the field encoder.

The root-UID Unix broker check is applied before any protocol bytes are sent.
Its UID authenticates the local broker only, not the worker or host. The service
checks client peer credentials and measured model/calibration digests, restricts
child environments, and retires failed masked work without releasing a result.
The package does not install an auto-start service or invent a worker address.
A measured platform adapter must supply its read-only configuration, UID 1001,
socket ACL, namespaces, seccomp policy and fixed worker route.

CI builds signed musl APKs for both architectures. Core self-tests cover field,
half conversion, preparation, prefix cache and bounded diagnostics. The recovered
Python tests cover compilation, late-tile failure, model policy and Q8 framing.
Installed ABI tests check broker/client UID rejection and status framing. Those
checks do not establish end-to-end masked GPU execution or platform admission.
