#!/bin/sh
set -eux
apk add --no-cache enclave-pocl opencl-icd-loader-dev opencl-headers
src=/src/reference/kvm-box/shield-compute/opencl
mkdir -p /out/tests
for test in event_errors half_convert half_tanh half_images; do
    # Qualify the CPU substrate before installing the logical-GPU frontend.
    sed 's/CL_DEVICE_TYPE_GPU/CL_DEVICE_TYPE_CPU/g' "$src/test_$test.cpp" >"/out/tests/$test.cpp"
    c++ -std=c++20 -O2 "/out/tests/$test.cpp" -lOpenCL -pthread -o "/out/tests/$test"
done
export POCL_DEBUG=error,warn
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}/usr/lib/enclave-pocl/lib:/usr/lib/enclave-pocl/lib/pocl"
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2 OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
for test in event_errors half_convert half_tanh half_images; do
    timeout 180 "/out/tests/$test" >"/out/$test.log" 2>&1
done
