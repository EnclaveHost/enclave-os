# Native desktop cursor lifetime

Keep the X11 root cursor resource owned by a live X connection. A short-lived
`xsetroot -cursor_name left_ptr` leaves root referencing a cursor whose client has
exited. In this VM, Xorg SECURITY's resource-access check returns BadAccess when
that client slot is empty. Reuse of the slot by another connection makes the
failure intermittent. Do not disable SECURITY to work around this.

`cursor-owner` creates a single themed arrow, keeps its X connection alive, and
repairs only root's default cursor every 100 ms. Application cursors, hidden
SDL cursors, and software game cursors remain controlled by their own windows.
Sunshine composites the native cursor normally. There is no cursor overlay and
no local fallback selected by the capture-state relay.

Build the amd64 guest binary against the guest-compatible X11 ABI:

```sh
cc -O2 -Wall -Wextra -Werror cursor-owner.c $(pkg-config --cflags --libs x11) -o cursor-owner
```

For the next signed image, use `kvm-box-native-root-build/3` with SHA256-pinned
`cursorOwner`, `cursorSupervisor`, and `cursorStart` inputs. The packager installs
them under `/usr/local/libexec/kvm-box/cursor`. Rebuild nsinit with the generated
home-defaults header: Fluxbox's rootCommand invokes start.py, which detaches the
supervisor. Older schema images keep working because this startup hook checks
that the executable exists. This helper is not a critical nsinit child; its
failure must not terminate the VM.

The supervisor enforces one instance, bounds logs, restarts a crashed child, and
replaces a child with a stale heartbeat. Retain the game-launcher fixes that
remove short-lived root cursor resets. Keep Sunshine's default cursor compositing
enabled and Moonlight's local fallback disabled. The automatic mouse-mode relay
controls absolute/relative input only; stale or missing hints preserve the last
valid mode.

Live validation on 2026-10-27: 12 sessions across OpenArena, LibreQuake, OpenHV and
VPX; 68 stages and 4,816 samples with no failed cursor reads. OpenArena gameplay
and menus reported relative/menu/relative. Firefox arrow/text/link shapes were
verified in the decoded Moonlight video. A stalled relay retained a visible
cursor for all 230 samples. A killed owner recovered in 0.128 s; a stopped owner
was replaced in 3.608 s. Critical desktop services were not restarted.

The live VM has the helper in its session home. The image-source changes have
been prepared and checked; they are not a newly signed or published image.
