# CUDA/HIP source compatibility

This is the canonical musl port of the recovered chipStar integration. The six
source revisions and their archive hashes are recorded by `prepare-source.py`.
The imported patch retains math fixes, failure propagation, queue cleanup and
Shield program provenance handling.

Only the OpenCL backend is built. Its runtime resolves the private Shield frontend;
it has no Level Zero backend or direct physical GPU route. CPU fallback tests
compile real HIP/CUDA samples, compare numerical output and exercise async streams.
The audited integer reference is rebuilt from `shield-opencl/gemm_i8_cuda.cu` and
checked against the structural IR rejection suite.

This provides source compatibility for the supported compiler/runtime subset. It
does not promise arbitrary CUDA binary compatibility. Native builds, installed
execution on both CPUs, masked-worker tests and adapter admission remain required.
