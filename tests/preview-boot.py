"""Boot the measured candidate with real dm-verity; remote disposable TCG only."""
import json, pathlib, subprocess
out = pathlib.Path('/out')
command = ['qemu-system-x86_64', '-machine', 'q35,accel=tcg', '-cpu', 'max',
    '-m', '2048M', '-smp', '2', '-nographic', '-no-reboot', '-nic', 'none',
    '-kernel', str(out/'kvm-boot/bzImage'), '-initrd', str(out/'preview-boot.cpio.gz'),
    '-append', 'console=ttyS0 rdinit=/init panic=-1', '-device', 'virtio-scsi-pci,id=scsi0']
for index, name in enumerate(('rootfs.squashfs', 'rootfs.verity')):
    command += ['-drive', f'file={out/name},if=none,id=disk{index},format=raw,readonly=on',
                '-device', f'scsi-hd,drive=disk{index},bus=scsi0.0,scsi-id={index}']
try:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    log, code = result.stdout.decode(errors='replace'), result.returncode
except subprocess.TimeoutExpired as error:
    log, code = (error.stdout or b'').decode(errors='replace'), 124
(out/'preview-boot.log').write_text(log)
if code or 'ENCLAVE_PREVIEW_ROOT_BOOT_OK' not in log or 'ENCLAVE_PREVIEW_ROOT_BOOT_FAILED' in log:
    print(log[-16000:]); raise SystemExit('Measured preview root did not pass kernel boot checks')
reports = [line.split('=', 1)[1] for line in log.splitlines() if line.startswith('ENCLAVE_PREVIEW_ROOT_RESULT=')]
assert len(reports) == 1
report = json.loads(reports[0])
assert len(report['checks']) == 6 and all(item['passed'] for item in report['checks'])
(out/'preview-boot.json').write_text(json.dumps(report, indent=2)+'\n')
print('PASS: measured preview root, kernel verity scan, policy refusal and installed command lines')
