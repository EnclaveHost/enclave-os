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
mkdir -p /home/builder/aports/enclave/enclave-shield-apps
cp /src/aports/enclave-shield-apps/APKBUILD /src/enclave-shield-compute-source.tar /home/builder/aports/enclave/enclave-shield-apps/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-shield-apps && abuild checksum && abuild -r' >/out/build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
cp /home/builder/aports/enclave/enclave-shield-apps/APKBUILD /out/APKBUILD
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-apps
sdk=/usr/lib/enclave-shield-apps
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2
export OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
mkdir -p /out/tests
for name in q8_views opencl_cpu_fallback; do
    c++ -std=c++17 -O2 -DGGML_MAX_NAME=128 \
        -I"$sdk/include" -I/src/shield-compute/sd/src \
        /src/components/shield-compute/test_$name.cpp \
        -L"$sdk/lib" -Wl,-rpath,"$sdk/lib" -lggml -lggml-base -o "/out/tests/$name"
    timeout 300 "/out/tests/$name" "$sdk/bin/libggml-opencl.so" "$sdk/bin/libggml-cpu.so" >"/out/$name.log" 2>&1
done
llama-cli --list-devices >/out/devices.log 2>&1
sd-cli --help >/out/sd-help.log 2>&1
