#!/bin/sh
set -eux
apk add --no-cache alpine-sdk sudo python3
for packages in /cpu /frontend; do
    cp "$packages"/*.pub /etc/apk/keys/
    printf '\n%s/repository\n' "$packages" >>/etc/apk/repositories
done
apk update
if [ -d /apps/repository ]; then
    cp /apps/*.pub /etc/apk/keys/
    printf '\n/apps/repository\n' >>/etc/apk/repositories
    cp -a /apps/repository /out/repository
    cp /apps/*.pub /apps/APKBUILD /out/
else
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
fi
apk add --no-cache enclave-shield-apps
sdk=/usr/lib/enclave-shield-apps
export POCL_DEVICES=pthread POCL_MAX_PTHREAD_COUNT=2
export POCL_DEBUG=error,warn
export OCL_ICD_VENDORS=/etc/OpenCL/vendors/pocl.icd
mkdir -p /out/tests
case "$(uname -m)" in
    riscv64) test_timeout=1800 ;;
    *) test_timeout=300 ;;
esac
cases="q8_views opencl_cpu_fallback"
if [ "${SHIELD_APPS_DIAGNOSTIC_ONLY:-0}" = 1 ]; then
    cases=opencl_cpu_fallback
    apk add --no-cache gdb
    ulimit -c 1048576
    printf '%s\n' '{"fullQualification":false,"diagnostic":"mixed CPU/OpenCL graph"}' >/out/diagnostic.json
fi
for name in $cases; do
    c++ -std=c++17 -O2 -DGGML_MAX_NAME=128 \
        -I"$sdk/include" -I/src/shield-compute/sd/src \
        /src/components/shield-compute/test_$name.cpp \
        -L"$sdk/lib" -Wl,-rpath,"$sdk/lib" -lggml -lggml-base -o "/out/tests/$name"
    result=0
    (cd /out && timeout "$test_timeout" "/out/tests/$name" "$sdk/bin/libggml-opencl.so" "$sdk/bin/libggml-cpu.so") >"/out/$name.log" 2>&1 || result=$?
    if [ "$result" != 0 ] && [ "${SHIELD_APPS_DIAGNOSTIC_ONLY:-0}" = 1 ]; then
        for core in /out/qemu_*.core; do
            [ -f "$core" ] || continue
            timeout 180 gdb -batch -ex 'set pagination off' -ex 'thread apply all bt' \
                -ex 'info registers' -ex 'x/12i $pc-16' "/out/tests/$name" "$core" \
                >"/out/$name-backtrace.log" 2>&1 || true
            rm -f "$core"
        done
    fi
    [ "$result" = 0 ] || exit "$result"
done
llama-cli --list-devices >/out/devices.log 2>&1
sd-cli --help >/out/sd-help.log 2>&1
