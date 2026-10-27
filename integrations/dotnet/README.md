# OpenHV RV64 runtime port

The x86 OpenHV APK uses Alpine's shared .NET 10 runtime. Alpine 3.24 has no
corresponding RV64 package. The dedicated remote workflow starts the remaining
port from dotnet/runtime `152ad965267240a3e23b6b3a24761e37aecc8c79`; its cross
toolchain explicitly recognizes `riscv64-alpine-linux-musl`.

This is a development runtime candidate, not a released replacement for .NET 10.
The workflow creates a target Alpine sysroot and uses the upstream cross-build
and bootstrap paths. It preserves source identity and build logs. A successful
compile must be followed by a signed APK, actual RV64 managed execution, W^X
policy tests, and OpenHV rendering/input/audio qualification. Any use of a newer
runtime for net10 assemblies must be explicit and qualified; this workflow does
not silently change the x86 game's runtime or mark RV64 support complete.

Upstream references:
- https://github.com/dotnet/runtime/blob/152ad965267240a3e23b6b3a24761e37aecc8c79/docs/workflow/building/coreclr/cross-building.md
- https://github.com/dotnet/runtime/blob/152ad965267240a3e23b6b3a24761e37aecc8c79/eng/common/cross/toolchain.cmake
