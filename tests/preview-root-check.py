"""Check the assembled read-only userland under its pinned KVM kernel policy."""
import ctypes, errno, json, os, pathlib, subprocess

assert os.getuid() == os.geteuid() == 1000
status = dict(line.split(':', 1) for line in pathlib.Path('/proc/self/status').read_text().splitlines())
assert status['NoNewPrivs'].strip() == '1' and status['Seccomp'].strip() == '2'
assert os.uname().release == '6.6.87.2-enclave-kvm-box'
assert pathlib.Path('/proc/sys/kernel/randomize_va_space').read_text().strip() == '2'
assert pathlib.Path('/etc/alpine-release').read_text().strip() == '3.24.3'
libc = ctypes.CDLL(None, use_errno=True)
libc.mmap.restype = ctypes.c_void_p
mapping = libc.mmap(None, 4096, 7, 0x22, -1, 0)
assert mapping == ctypes.c_void_p(-1).value and ctypes.get_errno() in (errno.EPERM, errno.ENOMEM)
commands = [
    ['/usr/bin/enclave-firefox', '--version'],
    ['/usr/bin/node', '--jitless', '-e', 'if (6*7 !== 42) process.exit(1)'],
    ['/usr/bin/llama-cli', '--list-devices'],
    ['/usr/bin/sd-cli', '--help'],
    ['/usr/lib/enclave-shield-hip/bin/hipcc', '--version'],
]
results = []
for command in commands:
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, (command, result.stdout[-2000:], result.stderr[-2000:])
    results.append({'command': command, 'passed': True})
for command in ('enclave-openarena', 'enclave-librequake', 'enclave-vpinball', 'enclave-openhv', 'enclave-sunshine'):
    assert os.access('/usr/bin/' + command, os.X_OK), command
print('ENCLAVE_PREVIEW_ROOT_RESULT=' + json.dumps({'checks': results, 'readOnlyRoot': True,
    'fullServiceStartup': False, 'runtimeAdmission': False, 'gpuExecution': False}))
