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

The native workflow builds candidate binaries and runs recovered gateway and
automation protocol tests. These artifacts are not an admitted image. Root
assembly, eudev/input confinement tests, complete service startup, nftables,
streaming and platform measurement/admission still need qualification. The RV64
adapter retains its separate boot boundary; this x86-only launcher does not
remove or bypass its architecture/kernel guards to claim support there.
