# OpenHV Alpine port

OpenHV 20250725 and its exact OpenRA release-20250330 engine are pinned in the
workflow. The original VM used this upstream code with local launcher/settings
customizations; no engine source patch was recovered. Those defaults are retained.

The port targets Alpine's shared .NET 10 runtime and system SDL2, OpenAL, Lua 5.1
and FreeType. It ships no glibc AppImage or private .NET runtime. Managed build
outputs and resolved NuGet lock files are retained; release promotion requires
reviewing and pinning the resulting dependency closure before offline rebuilds.
The launcher requires the shared Shield graphics environment and preserves W^X
runtime settings. Actual kernel-policy compatibility remains a separate gate.

RV64 remains pending: Alpine 3.24 has no packaged .NET/Mono runtime for this ISA.
The x86 package and CPU startup fixture do not complete the shared-game migration.
GeoIP is not fetched from an unpinned URL during the build; any optional database
must be separately pinned and licensed before inclusion. Network gameplay, content
loading, real input, sound and cursor recovery still require qualification.
