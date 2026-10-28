#!/bin/sh
set -eu
source=${1:?source directory}
output=${2:?output directory}
mkdir -p "$output"
# Inside the HIP builder, with the installed pinned toolchain, source at /src
# and a private writable /build. The reference comes from audited CUDA source,
# never from the candidate application or its kernel name.
/usr/lib/enclave-shield-hip/bin/cucc -c "$source/gemm_i8_cuda.cu" -o "$output"/gemm-reference.o
/usr/lib/llvm18/bin/llvm-objcopy --dump-section=.hip_fatbin="$output"/gemm-reference.bundle "$output"/gemm-reference.o
/usr/lib/llvm18/bin/clang-offload-bundler --unbundle --type=bc --targets=hip-spirv64----generic \
    --input="$output"/gemm-reference.bundle --output="$output"/gemm-reference.spv
llvm-spirv-18 -r "$output"/gemm-reference.spv -o "$output"/gemm-reference.bc
sha256sum "$source/gemm_i8_cuda.cu" "$output"/gemm-reference.spv "$output"/gemm-reference.bc \
    > "$output"/gemm-reference.sha256
