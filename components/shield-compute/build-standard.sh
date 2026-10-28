#!/bin/sh
set -eu
JOBS=${JOBS:-2}
BUILD_ROOT=${ENCLAVE_BUILD_ROOT:-/build}
INPUT_ROOT=${ENCLAVE_INPUT_ROOT:-/input}
mkdir -p "$BUILD_ROOT/src" "$BUILD_ROOT/out/bin" "$BUILD_ROOT/out/lib" "$BUILD_ROOT/out/include"
cp -a "$INPUT_ROOT/llama" "$INPUT_ROOT/sd" "$BUILD_ROOT/src/"
LLAMA="$BUILD_ROOT/src/llama"
SD="$BUILD_ROOT/src/sd"
cmake -S "$LLAMA" -B "$BUILD_ROOT/llama" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
    -DGGML_BACKEND_DL=ON -DGGML_CPU_REPACK=OFF -DGGML_NATIVE=OFF \
    -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_RVV=OFF -DGGML_FMA=OFF -DGGML_F16C=OFF \
    -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_OPENCL=ON \
    -DGGML_OPENCL_USE_ADRENO_KERNELS=OFF -DGGML_OPENCL_EMBED_KERNELS=ON \
    -DOpenCL_LIBRARY=/usr/lib/enclave-shield-opencl/lib/libOpenCL.so \
    -DGGML_BUILD_TESTS=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TOOLS=ON -DLLAMA_BUILD_SERVER=ON -DLLAMA_BUILD_APP=OFF \
    -DLLAMA_CURL=OFF -DLLAMA_OPENSSL=OFF \
    -DCMAKE_C_FLAGS=-DGGML_MAX_NAME=128 -DCMAKE_CXX_FLAGS=-DGGML_MAX_NAME=128 \
    -DCMAKE_INSTALL_PREFIX="$BUILD_ROOT/prefix"
cmake --build "$BUILD_ROOT/llama" --target llama-cli ggml-cpu ggml-opencl -j "$JOBS"
cmake --install "$BUILD_ROOT/llama/ggml"
cmake -S "$SD" -B "$BUILD_ROOT/sd" -G Ninja -DCMAKE_BUILD_TYPE=Release \
    -DSD_BUILD_SHARED_LIBS=ON -DSD_USE_SYSTEM_GGML=ON -DSD_BUILD_EXAMPLES=ON \
    -DSD_WEBP=OFF -DSD_WEBM=OFF -DSD_CUDA=OFF -DSD_VULKAN=OFF \
    -DCMAKE_PREFIX_PATH="$BUILD_ROOT/prefix" \
    "-DCMAKE_C_FLAGS=-DGGML_MAX_NAME=128 -I$BUILD_ROOT/prefix/include" \
    "-DCMAKE_CXX_FLAGS=-DGGML_MAX_NAME=128 -I$BUILD_ROOT/prefix/include"
cmake --build "$BUILD_ROOT/sd" --target sd-cli -j "$JOBS"
cp -a "$BUILD_ROOT/llama/bin/"lib*.so* "$BUILD_ROOT/sd/bin/"libstable-diffusion.so* "$BUILD_ROOT/out/lib/"
mv "$BUILD_ROOT/out/lib/libggml-cpu.so" "$BUILD_ROOT/out/lib/libggml-opencl.so" "$BUILD_ROOT/out/bin/"
cp "$BUILD_ROOT/llama/bin/llama-cli" "$BUILD_ROOT/sd/bin/sd-cli" "$BUILD_ROOT/out/bin/"
cp -a "$BUILD_ROOT/prefix/include/." "$BUILD_ROOT/out/include/"
cp "$INPUT_ROOT/source-provenance.json" "$INPUT_ROOT/sources.lock.json" "$BUILD_ROOT/out/"
cp "$LLAMA/LICENSE" "$BUILD_ROOT/out/LICENSE.llama"
cp "$SD/LICENSE" "$BUILD_ROOT/out/LICENSE.sd"
for f in "$BUILD_ROOT/out/bin/"* "$BUILD_ROOT/out/lib/"*.so*; do
    [ -L "$f" ] && continue
    patchelf --set-rpath '$ORIGIN:$ORIGIN/../lib:/usr/lib/enclave-shield-opencl/lib' "$f"
done
python3 - "$BUILD_ROOT/out" <<'PY'
import hashlib, json, pathlib, subprocess, sys
root = pathlib.Path(sys.argv[1])
for path in root.rglob('*'):
    if not path.is_file() or path.is_symlink() or path.read_bytes()[:4] != b'\x7fELF':
        continue
    dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
    assert not any(x in dynamic.lower() for x in ('libcuda', 'libvulkan', 'libggml-cuda')), path
    segments = subprocess.check_output(['readelf', '-lW', str(path)], text=True)
    assert not any('GNU_STACK' in line and 'RWE' in line for line in segments.splitlines()), path
files = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(root.rglob('*')) if p.is_file()}
(root / 'files.sha256.json').write_text(json.dumps(files, indent=2) + '\n')
PY
