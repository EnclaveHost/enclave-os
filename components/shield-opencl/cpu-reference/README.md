# CPU execution reference

`conv2d.cl` is copied unchanged from `ggml-org/llama.cpp` commit
`ddd4ec1428a6201e18975ea52b07c71e0f9aef26`, under
`ggml/src/ggml-opencl/kernels`. SHA256: `f62779e3aefedadfb516d0fda3872cf13d8eecb1a55507edc5177879bfe5d712`.
The MIT license is retained in `../q8-reference/LICENSE`.

The conformance test compares five convolution shapes against independent NCHW
arithmetic and checks output guards. This is a CPU fallback fixture, not a
masked-operation authorization reference.
