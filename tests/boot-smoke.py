#!/usr/bin/env python3
"""Real kernel boot of the shared minimal userland under system emulation."""
import base64,gzip,json,os,pathlib,subprocess,sys
arch=sys.argv[1];out=pathlib.Path('out');kernel=out/'smoke-kernel'
if arch=='x86_64':
    cmd=['qemu-system-x86_64','-machine','q35,accel=tcg','-cpu','max']
elif arch=='riscv64':
    cmd=['qemu-system-riscv64','-machine','virt','-cpu','rv64','-bios','default']
    if kernel.read_bytes()[:2]==b'\x1f\x8b':
        raw=out/'smoke-kernel.raw';raw.write_bytes(gzip.decompress(kernel.read_bytes()));kernel=raw
else:raise SystemExit('unsupported architecture')
managed=os.environ.get('ENCLAVE_MANAGED_POLICY_TEST')=='1'
browser=os.environ.get('ENCLAVE_BROWSER_POLICY_TEST')=='1'
cmd+=['-m','2048M' if browser else ('1024M' if managed else '512M'),'-smp','2','-nographic','-no-reboot','-nic','none',
      '-kernel',str(kernel),'-initrd',str(out/'smoke-initramfs.cpio.gz'),
      '-append','console=ttyS0 rdinit=/init panic=-1']
try:
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=600 if browser else (300 if managed else 120))
    log=result.stdout.decode(errors='replace');code=result.returncode
except subprocess.TimeoutExpired as e:
    log=(e.stdout or b'').decode(errors='replace');code=124
(out/'boot.log').write_text(log)
if browser:
    if 'ENCLAVE_BROWSER_POLICY_OK' not in log:
        print(log[-16000:]);raise SystemExit('Browser kernel policy checks did not pass')
    reports=[line.split('=',1)[1] for line in log.splitlines() if line.startswith('ENCLAVE_BROWSER_RESULTS=')]
    assert len(reports)==1
    report=json.loads(reports[0])
    assert len(report['results'])==9 and all(r['passed'] is True for r in report['results'])
    picture=base64.b64decode(report.pop('screenshot'),validate=True)
    assert picture.startswith(b'\x89PNG\r\n\x1a\n') and 100<len(picture)<4*1024*1024
    (out/'browser-page.png').write_bytes(picture)
    (out/'browser-results.json').write_text(json.dumps(report,indent=2)+'\n')
if managed and 'ENCLAVE_MANAGED_POLICY_OK' not in log:
    print(log[-16000:]);raise SystemExit('Managed runtime policy checks did not pass')
if os.environ.get('ENCLAVE_POLICY_TEST') == '1' and arch == 'x86_64' and 'ENCLAVE_NATIVE_ROLES_OK' not in log:
    print(log[-16000:]);raise SystemExit('Native role/udev confinement tests did not pass')
if code or f'ENCLAVE_BOOT_OK {arch}' not in log or (os.environ.get('ENCLAVE_POLICY_TEST') == '1' and 'ENCLAVE_POLICY_OK' not in log):
    print(log[-16000:]);raise SystemExit(f'{arch}: boot failed (exit {code})')
print(f'PASS: {arch} kernel boot, Enclave userland, ASLR, shutdown')
