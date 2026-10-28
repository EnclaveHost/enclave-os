# Alpine native platform candidate

This is the editable x86 KVM adapter port. `recovered-source.json` records the
imported versions; the reference tree remains unchanged. It retains the exact
kernel admission check, read-only root preparation, fresh X/Sunshine credentials,
role UIDs, capability removal, authenticated sockets and bounded supervision.
The role filter comes from the canonical `components/platform-policy` sources.

Paths now select Alpine Xorg/eudev and the private Enclave graphics, compute and
streaming packages. The embedded initial home is generated from the shared
desktop skeleton rather than the old Debian home. The desktop inherits the
supervised session bus instead of spawning a second one.

`shield/` retains the two public model tensor policies, calibration files and
model-volume measurement from the recovered native image inputs. Only the SDK
and masking-core installation paths in `native-service.json` change for Alpine;
model hashes, tensor hashes, worker route, peer UIDs and constant allowlist stay
unchanged. `recovered-source.json` pins these inputs. The model payloads remain a
separate measured read-only volume and are not bundled or downloaded by this
package. The service still verifies the actual mounted models before becoming
ready. Retaining these policies does not qualify new binaries or grant platform
admission; those require the full startup and masked numerical tests.

The native workflow builds candidate binaries and runs recovered gateway and
automation protocol tests. These artifacts are not an admitted image. Root
assembly, eudev/input confinement tests, complete service startup, nftables,
streaming and platform measurement/admission still need qualification. The RV64
adapter retains its separate boot boundary; this x86-only launcher does not
remove or bypass its architecture/kernel guards to claim support there.

The current KVM boot/monitor ABI opens `nsinit` and `gateway` beneath
`/usr/local/libexec/kvm-box` without following symlinks, and loads `nft_ct.ko`
from that same directory. `tools/kvm_boot_inputs.py` creates regular hard links
to the Alpine package helpers and adds the exact module from the pinned preview
kernel build. It also exports the static helpers and kernel files for subsequent
platform archive construction. Hash mismatches fail before root modification.
These inputs alone are not a bootable or admitted platform archive.

After measuring and corruption-testing the root, `tools/kvm_profile.py` emits
the launcher's canonical `enclave-native-desktop-profile/1` descriptor with the
new kernel/root measurements. `profiles/preview-kvm-retained.json` preserves the
recovered controller and public model-volume pins from the native startup
fixture. The controller pin was rechecked against the retained Wasm binary;
model bytes are not recopied or declared freshly verified. Neither payload is
included in this OS artifact. `kvm-preview-status.json` explicitly leaves platform
archive construction, runtime admission and production qualification unfinished.

The preview workflow also boots its measured SquashFS through kernel dm-verity
in a separate TCG guest, reads the entire verified block device, checks the root
is read-only, and exercises installed browser/compute command lines after the
unprivileged memory policy is applied. Its 2 GiB guest is a userland compatibility
fixture; it does not invoke the native supervisor or reduce its 8 GiB minimum.
Full service startup, model/worker integration and platform admission remain
required before a usable KVM Box instance can be offered.
