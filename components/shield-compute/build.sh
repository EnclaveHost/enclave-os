#!/bin/sh
set -eu
JOBS=${JOBS:-2}
BUILD_ROOT=${ENCLAVE_BUILD_ROOT:-/build}
INPUT_ROOT=${ENCLAVE_INPUT_ROOT:-/input}
export ENCLAVE_BUILD_ROOT="$BUILD_ROOT"
mkdir -p ${BUILD_ROOT}/src ${BUILD_ROOT}/out/lib/backends ${BUILD_ROOT}/out/bin ${BUILD_ROOT}/out/include
cp -a ${INPUT_ROOT}/llama ${INPUT_ROOT}/sd ${INPUT_ROOT}/enclave ${INPUT_ROOT}/shield ${BUILD_ROOT}/src/
LLAMA=${BUILD_ROOT}/src/llama
SD=${BUILD_ROOT}/src/sd
SHIELD=${BUILD_ROOT}/src/shield/wasm/ggml-shielded
python3 "${INPUT_ROOT}/portable.py" "$SHIELD"
cmake -S "$LLAMA" -B ${BUILD_ROOT}/llama -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
    -DGGML_BACKEND_DL=ON -DGGML_CPU_REPACK=OFF -DGGML_NATIVE=OFF -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_RVV=OFF \
    -DGGML_FMA=OFF -DGGML_F16C=OFF -DGGML_CUDA=OFF -DGGML_VULKAN=OFF \
    -DGGML_BUILD_TESTS=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_APP=OFF \
    -DLLAMA_CURL=OFF -DLLAMA_OPENSSL=OFF \
    -DCMAKE_C_FLAGS=-DGGML_MAX_NAME=128 -DCMAKE_CXX_FLAGS=-DGGML_MAX_NAME=128 \
    -DCMAKE_INSTALL_PREFIX=${BUILD_ROOT}/prefix
cmake --build ${BUILD_ROOT}/llama --target llama-cli ggml-cpu -j "$JOBS"
cmake --install ${BUILD_ROOT}/llama/ggml
cmake -S "$SD" -B ${BUILD_ROOT}/sd -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DSD_BUILD_SHARED_LIBS=ON -DSD_USE_SYSTEM_GGML=ON -DSD_BUILD_EXAMPLES=ON \
    -DSD_WEBP=OFF -DSD_WEBM=OFF -DSD_CUDA=OFF -DSD_VULKAN=OFF \
    -DCMAKE_PREFIX_PATH=${BUILD_ROOT}/prefix \
    "-DCMAKE_C_FLAGS=-DGGML_MAX_NAME=128 -I${BUILD_ROOT}/prefix/include" \
    "-DCMAKE_CXX_FLAGS=-DGGML_MAX_NAME=128 -I${BUILD_ROOT}/prefix/include"
cmake --build ${BUILD_ROOT}/sd --target sd-cli -j "$JOBS"
make -C "$SHIELD" -j "$JOBS" libggml-shielded.so shielded-run shielded-probe sd-calib \
    GGML_SRC="$LLAMA" GGML_LIB=${BUILD_ROOT}/llama/bin \
    SD_SRC="$SD" SD_LIB=${BUILD_ROOT}/sd/bin "LDLIBS=-lm -lpthread -L${BUILD_ROOT}/llama/bin" \
    'CFLAGS=-O2 -std=gnu11 -Wall -Wextra -fPIC -fno-math-errno' \
    'CXXFLAGS=-O2 -std=c++17 -Wall -Wextra -fPIC -fno-math-errno -DGGML_MAX_NAME=128'
cp -a ${BUILD_ROOT}/llama/bin/lib*.so* ${BUILD_ROOT}/sd/bin/libstable-diffusion.so* ${BUILD_ROOT}/out/lib/
mv ${BUILD_ROOT}/out/lib/libggml-cpu.so ${BUILD_ROOT}/out/lib/backends/
cp "$SHIELD/libggml-shielded.so" ${BUILD_ROOT}/out/lib/backends/
cp ${BUILD_ROOT}/llama/bin/llama-cli ${BUILD_ROOT}/sd/bin/sd-cli "$SHIELD/shielded-run" "$SHIELD/shielded-probe" "$SHIELD/sd-calib" ${BUILD_ROOT}/out/bin/
c++ -shared -fPIC -O2 -std=c++17 -DGGML_MAX_NAME=128 \
    -I"$LLAMA/ggml/include" -I"$LLAMA/vendor" -I"$SHIELD" ${INPUT_ROOT}/bootstrap.cpp \
    -L${BUILD_ROOT}/llama/bin -lggml -lggml-base -lcrypto -ldl \
    -Wl,-z,relro,-z,now,-z,noexecstack -o ${BUILD_ROOT}/out/lib/libenclave-shield-bootstrap.so
cp -a ${BUILD_ROOT}/prefix/include/. ${BUILD_ROOT}/out/include/
cp "$LLAMA/include/llama.h" "$SD/include/stable-diffusion.h" ${BUILD_ROOT}/out/include/
cp ${INPUT_ROOT}/source-provenance.json ${INPUT_ROOT}/sources.lock.json ${BUILD_ROOT}/out/
cp "$LLAMA/LICENSE" ${BUILD_ROOT}/out/LICENSE.llama
cp "$SD/LICENSE" ${BUILD_ROOT}/out/LICENSE.sd
cp ${BUILD_ROOT}/src/shield/LICENSE ${BUILD_ROOT}/out/LICENSE.shield
for f in ${BUILD_ROOT}/out/bin/* ${BUILD_ROOT}/out/lib/*.so* ${BUILD_ROOT}/out/lib/backends/*.so*; do
    [ -L "$f" ] && continue
    case "$f" in
        */bin/*) patchelf --set-rpath '$ORIGIN/../lib' "$f" ;;
        */backends/*) patchelf --set-rpath '$ORIGIN/..' "$f" ;;
        *) patchelf --set-rpath '$ORIGIN' "$f" ;;
    esac
done
python3 - <<'PY'
import hashlib,json,subprocess,os
from pathlib import Path
root=Path(os.environ['ENCLAVE_BUILD_ROOT'])/'out'
for path in root.rglob('*'):
    if not path.is_file() or path.is_symlink(): continue
    if path.read_bytes()[:4] != b'\x7fELF': continue
    dyn=subprocess.check_output(['readelf','-d',str(path)],text=True)
    if any(x in dyn.lower() for x in ('libcuda','libvulkan','libggml-cuda')):
        raise SystemExit('unmasked GPU dependency: '+str(path))
    segments=subprocess.check_output(['readelf','-lW',str(path)],text=True)
    if any('GNU_STACK' in line and 'RWE' in line for line in segments.splitlines()):
        raise SystemExit('executable stack: '+str(path))
files={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()
       for f in sorted(root.rglob('*')) if f.is_file() and f.name != 'files.sha256.json'}
(root/'files.sha256.json').write_text(json.dumps(files,indent=2)+'\n')
PY
