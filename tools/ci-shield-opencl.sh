#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
cp /packages/*.pub /etc/apk/keys/
printf '\n/packages/repository\n' >>/etc/apk/repositories
apk update
adduser -D builder
addgroup builder abuild
printf 'builder ALL=(ALL) NOPASSWD: ALL\n' >/etc/sudoers.d/builder
mkdir -p /home/builder/aports/enclave/enclave-shield-opencl
cp /src/aports/enclave-shield-opencl/APKBUILD /src/enclave-shield-opencl-source.tar /home/builder/aports/enclave/enclave-shield-opencl/
chown -R builder:builder /home/builder
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /etc/apk/keys/
su builder -c 'cd /home/builder/aports/enclave/enclave-shield-opencl && abuild checksum && abuild -r' >/out/build.log 2>&1
cp -a /home/builder/packages/enclave /out/repository
cp /home/builder/.abuild/*.pub /out/
cp /home/builder/aports/enclave/enclave-shield-opencl/APKBUILD /out/APKBUILD
printf '\n/home/builder/packages/enclave\n' >>/etc/apk/repositories
apk add --no-cache enclave-shield-opencl opencl-icd-loader-dev opencl-headers
python3 /src/tests/installed-q8-compiler.py >/out/installed-q8.log 2>&1
mkdir /out/tests
export LD_LIBRARY_PATH=/usr/lib/enclave-shield-opencl/lib
export POCL_DEBUG=error,warn
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2 OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
for test in event_errors half_convert half_tanh half_images svm conv2d; do
    c++ -std=c++20 -O2 '-DSHIELD_TEST_KERNEL="/src/components/shield-opencl/gemm_i8.cl"' "/src/components/shield-opencl/test_$test.cpp" -L/usr/lib/enclave-shield-opencl/lib -lOpenCL -pthread -o "/out/tests/$test"
    case "$test" in
        svm) timeout 180 /out/tests/svm svm cpu-compat >/out/svm.log 2>&1 ;;
        conv2d) timeout 180 /out/tests/conv2d /src/components/shield-opencl/cpu-reference/conv2d.cl >/out/conv2d.log 2>&1 ;;
        *) timeout 180 "/out/tests/$test" >"/out/$test.log" 2>&1 ;;
    esac
done
for mode in svm-subrange svm-mixed svm-rebind dependency-failure; do
    timeout 180 /out/tests/svm "$mode" cpu-compat >"/out/$mode.log" 2>&1
done
