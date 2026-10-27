# Persistent desktop cursor

The cursor owner keeps its X connection alive so Xorg SECURITY can authorize
cursor-image reads after application windows close. Short-lived xsetroot cursor
owners caused intermittent BadAccess failures in the original native desktop.
Do not disable Xorg SECURITY as a workaround.

The portable APK builds cursor-owner against musl/libX11 for x86-64 and RV64.
It installs the executable and supervisor under /usr/libexec/enclave-os/cursor.
The shared desktop session starts the supervisor after authenticated X is ready.
DISPLAY and XAUTHORITY are inherited from the platform adapter; no Debian path
or fixed display number is assumed. Only root-window defaults are repaired;
application cursor shapes and hidden game cursors retain their normal behavior.

The existing Python runtime is shared with desktop automation and noVNC. The
supervisor enforces a singleton, bounds helper logs, backs off repeated crashes
and recovers stalled heartbeats. It is not a critical VM-lifetime process.
Game launchers must not replace root's cursor with a short-lived owner.

CI tests authenticated X, rejected missing credentials, XFixes reads, singleton
ownership, SIGKILL recovery, SIGSTOP recovery and FreeDoom startup. Historical
live Moonlight validation and original image-builder integration are preserved
in reference/kvm-box/guest/native/cursor/README.md. Alpine Moonlight deployment
still requires its own end-to-end qualification.
