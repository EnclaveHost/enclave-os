# Alpine OpenCL substrate

The CPU ICD is built from the same PoCL 6.0 revision as the measured Debian image,
with the recovered callback, half conversion/tanh/image and vectorizer patches.
Only CPU devices are built; remote, CUDA, Vulkan, HSA and accelerator drivers are
explicitly disabled. The private install uses LLVM 18 and a separately pinned
LLVM 18 SPIR-V translator, avoiding ABI mixing with Mesa's LLVM 22.

`opencl-cpu.yml` builds and installs signed APKs and exercises actual OpenCL event
callbacks and half operations. It does not claim masked GPU execution. The normal
OpenCL frontend, source/IR recognizer, authenticated service and masked worker still
require musl porting and their own end-to-end qualification before release.
