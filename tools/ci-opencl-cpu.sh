#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
for name in llvm-spirv18 pocl; do
    cp -a "/src/aports/enclave-$name" /home/builder/aports/enclave/
done
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
for name in llvm-spirv18 pocl; do
    su builder -c "cd /home/builder/aports/enclave/enclave-$name && abuild -r" >"/out/$name-build.log" 2>&1
    if [ "$name" = llvm-spirv18 ]; then
        printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
    fi
    apk update
done
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
apk add --no-cache enclave-pocl opencl-icd-loader-dev
src=/src/reference/kvm-box/shield-compute/opencl
mkdir -p /out/tests
for test in event_errors half_convert half_tanh half_images; do
    c++ -std=c++20 -O2 "$src/test_$test.cpp" -lOpenCL -pthread -o "/out/tests/$test"
done
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2 OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
for test in event_errors half_convert half_tanh half_images; do
    timeout 180 "/out/tests/$test" >"/out/$test.log" 2>&1
done
