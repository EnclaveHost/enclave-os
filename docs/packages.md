# Package repository and footprint policy

The repository already has real APKBUILD recipes, native builds and signed installation checks. A production package service is a later deployment step, not a placeholder URL added to users' machines.

## Package boundaries

Use a single copy of each shared library/runtime. Put applications, engines and content into separate packages where upgrades or footprint warrant it. Keep compilers, headers, tests, source archives and build caches out of installed images. Do not ship a glibc compatibility distribution just to reuse Debian binaries. Rebuild custom components for musl instead.

Images have a small common core and a full desktop preset. Package selection is explicit, identical across architectures except display drivers, and recorded with the final dependency inventory. Do not remove fonts, codecs, certificates, locales or accessibility support blindly to improve a headline size number. Measure the benefit and preserve needed functionality.

Read-only compression belongs to the final platform image step. Avoid copying root contents into RAM; use bounded writable overlays for state. Models and large game data belong in separately managed, integrity-checked storage so rebuilding the OS does not duplicate them or consume the small writable home volume. Existing runtime-only /dev/shm game workarounds are not the desired package layout.

## Trust and reproducibility

The Alpine bootstrap and builder are digest-pinned. Custom source archives have deterministic paths, ownership, timestamps and SHA-512 checksums; update them intentionally with `tools/stage-aports.py staging --update-checksums` when source changes. Imports have independent SHA-256 provenance.

Upstream package repositories remain the maintained Alpine 3.24 branch. **Transitive APK versions are not fully locked yet**: each build records the installed database. Bit-for-bit release reproduction requires retaining/snapshotting those exact APKs and indexes before release. A pinned container alone does not make every dependency reproducible.

CI generates an ephemeral signing key, publishes only its public half with the development repository, and verifies package/index signatures during installation. The public test key is then removed from assembled images. A production release must use an externally managed release key, an explicit trust-rotation policy and immutable versioned repository paths. Never use `--allow-untrusted` as the installation workflow.

A production publisher should stage packages, construct and sign APKINDEX for each architecture, verify a clean install, and atomically promote the completed release. Do not publish an index while its packages are still uploading. CI artifacts are intentionally short-lived development output, not an update feed.
