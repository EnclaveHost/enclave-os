#!/bin/sh
set -eux
apk add --no-cache enclave-pocl opencl-icd-loader-dev opencl-headers gdb
src=/src/reference/kvm-box/shield-compute/opencl
mkdir -p /out/tests
for test in event_errors half_convert half_tanh half_images; do
    # Qualify the CPU substrate before installing the logical-GPU frontend.
    sed 's/CL_DEVICE_TYPE_GPU/CL_DEVICE_TYPE_CPU/g' "$src/test_$test.cpp" >"/out/tests/$test.cpp"
    c++ -std=c++20 -O2 "/out/tests/$test.cpp" -lOpenCL -pthread -o "/out/tests/$test"
done
export POCL_DEBUG=error,warn
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2 OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
status=0
test_timeout=180
# RV64 user emulation also translates the kernel compiler. Keep every case,
# but allow its cold image-kernel compilation to finish.
if [ "$(uname -m)" = riscv64 ]; then test_timeout=900; fi
for test in event_errors half_convert half_tanh half_images; do
    started=$(date +%s)
    test_status=0
    timeout "$test_timeout" "/out/tests/$test" >"/out/$test.log" 2>&1 || test_status=$?
    printf '%s exit=%s elapsed=%ss deadline=%ss\n' "$test" "$test_status" "$(( $(date +%s) - started ))" "$test_timeout" >>/out/test-times.log
    if [ "$test_status" != 0 ]; then
        status=1
        if [ "$(uname -m)" != riscv64 ]; then
            timeout 180 gdb --batch -ex run -ex 'thread apply all bt' -ex 'info registers' -ex 'x/24i $pc-32' --args "/out/tests/$test" >"/out/$test-debug.log" 2>&1 || true
        fi
    fi
done
if [ "$status" != 0 ]; then
    tar -czf /out/pocl-cache.tar.gz -C /root/.cache/pocl kcache
fi
exit "$status"
