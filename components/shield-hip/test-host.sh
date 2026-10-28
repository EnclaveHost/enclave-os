#!/bin/sh
set -eu
# The caller supplies only the CPU ICD and Shield frontend. No host GPU device
# or worker endpoint is required: these tests exercise CPU execution, including
# the integer GEMM's explicit non-offloadable K=31 shape.
export CHIP_BE=opencl CHIP_DEVICE_TYPE=gpu CHIP_LOGLEVEL=crit
for device in /dev/dri /dev/kfd /dev/nvidia*; do
    if test -e "$device"; then
        printf 'Unexpected physical GPU device in CPU fallback test: %s\n' "$device" >&2
        exit 1
    fi
done
mkdir -p /tests
cd /tests
/usr/lib/enclave-shield-hip/bin/hipcc /src/chipStar-source/samples/0_MatrixTranspose/MatrixTranspose.cpp \
    -o /tests/matrix-transpose > /tests/matrix-transpose-build.log 2>&1
timeout 90 /tests/matrix-transpose > /tests/matrix-transpose-run.log 2>&1
printf '%s\n' 'HIP matrix transpose: passed'
for name in vectorAdd matrixMul asyncAPI; do
    /usr/lib/enclave-shield-hip/bin/cucc -I/src/chipStar-source/samples/cuda_samples/Common \
        "/src/chipStar-source/samples/cuda_samples/0_Simple/$name/$name.cu" \
        -o "/tests/$name" > "/tests/$name-build.log" 2>&1
    timeout 90 "/tests/$name" > "/tests/$name-run.log" 2>&1
    printf 'CUDA %s: passed\n' "$name"
done
/usr/lib/enclave-shield-hip/bin/cucc /src/components/shield-hip/test_cuda.cu -o /tests/cuda-gemm \
    > /tests/cuda-gemm-build.log 2>&1
timeout 90 /tests/cuda-gemm cpu-compat > /tests/cuda-gemm-run.log 2>&1
printf '%s\n' 'CUDA integer GEMM: passed'
/usr/lib/enclave-shield-hip/bin/hipcc /src/components/shield-hip/test_math.cpp -o /tests/hip-math \
    > /tests/hip-math-build.log 2>&1
timeout 90 /tests/hip-math > /tests/hip-math-run.log 2>&1
printf '%s\n' 'HIP host/device pi-scaled math: passed'
