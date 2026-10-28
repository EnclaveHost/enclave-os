#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
for packages in /cpu /frontend /hip; do
    cp "$packages"/*.pub /etc/apk/keys/
    printf '\n%s/repository\n' "$packages" >>/etc/apk/repositories
done
apk add --no-cache enclave-shield-hip
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave
cp -a /src/aports/enclave-shield-ir-reference /home/builder/aports/enclave/
cp /hip/reference/gemm-reference.bc /hip/reference/gemm-reference.spv /home/builder/aports/enclave/enclave-shield-ir-reference/
printf '%s\n' '457de84b5379139eb9eaa67a70e35d3ab2c050869fa7dd61490fc7787317596f  /src/components/shield-opencl/gemm_i8_cuda.cu' | sha256sum -c -
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-shield-ir-reference && abuild -r' >/out/build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-ir-reference
mkdir -p /tests
/usr/lib/enclave-shield-hip/bin/cucc -c /src/components/shield-hip/test_cuda.cu -o /tests/cuda-gemm.o
/usr/lib/llvm18/bin/llvm-objcopy --dump-section=.hip_fatbin=/tests/cuda-gemm.bundle /tests/cuda-gemm.o
/usr/lib/llvm18/bin/clang-offload-bundler --unbundle --type=bc --targets=hip-spirv64----generic \
    --input=/tests/cuda-gemm.bundle --output=/tests/cuda-gemm.spv
llvm-spirv-18 -r /tests/cuda-gemm.spv -o /tests/cuda-gemm-reverse.bc
export SHIELD_OPENCL_PACKAGE=/usr/lib/enclave-shield-opencl
export SHIELD_IR_REFERENCE=/usr/lib/enclave-shield-opencl/gemm-reference.bc
python3 /src/components/shield-opencl/test_ir_compiler.py -v >/out/installed-ir-tests.log 2>&1
cp /hip/reference/gemm-reference.sha256 /out/
