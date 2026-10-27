#!/usr/bin/env python3
"""Real kernel boot of the shared minimal userland under system emulation."""
import gzip,pathlib,subprocess,sys
arch=sys.argv[1];out=pathlib.Path('out');kernel=out/'smoke-kernel'
if arch=='x86_64':
    cmd=['qemu-system-x86_64','-machine','q35,accel=tcg','-cpu','max']
elif arch=='riscv64':
    cmd=['qemu-system-riscv64','-machine','virt','-cpu','rv64','-bios','default']
    if kernel.read_bytes()[:2]==b'\x1f\x8b':
        raw=out/'smoke-kernel.raw';raw.write_bytes(gzip.decompress(kernel.read_bytes()));kernel=raw
else:raise SystemExit('unsupported architecture')
cmd+=['-m','512M','-smp','2','-nographic','-no-reboot','-nic','none',
      '-kernel',str(kernel),'-initrd',str(out/'smoke-initramfs.cpio.gz'),
      '-append','console=ttyS0 rdinit=/init panic=-1']
try:
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    log=result.stdout.decode(errors='replace');code=result.returncode
except subprocess.TimeoutExpired as e:
    log=(e.stdout or b'').decode(errors='replace');code=124
(out/'boot.log').write_text(log)
if code or f'ENCLAVE_BOOT_OK {arch}' not in log:
    print(log[-16000:]);raise SystemExit(f'{arch}: boot failed (exit {code})')
print(f'PASS: {arch} kernel boot, Enclave userland, ASLR, shutdown')
