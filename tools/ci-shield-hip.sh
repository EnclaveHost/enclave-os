#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
for packages in /cpu /frontend; do
    cp "$packages"/*.pub /etc/apk/keys/
    printf '\n%s/repository\n' "$packages" >>/etc/apk/repositories
done
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave/enclave-shield-hip
cp /src/aports/enclave-shield-hip/APKBUILD /src/chipStar-source.tar \
    /src/components/shield-hip/chipstar-glibc.patch /home/builder/aports/enclave/enclave-shield-hip/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-shield-hip && abuild checksum && abuild -r' >/out/build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
cp /home/builder/aports/enclave/enclave-shield-hip/APKBUILD /out/APKBUILD
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-hip opencl-headers
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2 OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
export LD_LIBRARY_PATH=/usr/lib/enclave-shield-opencl/lib
mkdir -p /tests
sh /src/components/shield-hip/test-host.sh >/out/runtime.log 2>&1 || { cp -a /tests /out/; exit 1; }
cp -a /tests /out/
sh /src/components/shield-opencl/build-ir-reference.sh /src/components/shield-opencl /out/reference >/out/reference-build.log 2>&1
cp -a /src/components/shield-opencl /tmp/opencl-tests
cp /usr/lib/enclave-shield-opencl/ir-compiler /tmp/opencl-tests/
cp /out/reference/gemm-reference.bc /out/reference/gemm-reference.spv /tmp/opencl-tests/
cd /tmp/opencl-tests
SHIELD_IR_REFERENCE=/tmp/opencl-tests/gemm-reference.bc python3 -m unittest -v test_ir_compiler >/out/ir-tests.log 2>&1
