"""Exercise Python FFI and callbacks after installing the actual role policy."""
import ctypes as C
import errno
import json
import os
import pathlib

assert os.getuid() == os.geteuid() == 1000
status = dict(line.split(':', 1) for line in pathlib.Path('/proc/self/status').read_text().splitlines())
assert status['NoNewPrivs'].strip() == '1' and status['Seccomp'].strip() == '2'
libc = C.CDLL(None, use_errno=True)
libc.mmap.restype = C.c_void_p
assert libc.mmap(None, 4096, 7, 0x22, -1, 0) == C.c_void_p(-1).value
assert C.get_errno() == errno.EPERM
callback_type = C.CFUNCTYPE(C.c_int, C.c_int)
callbacks = [callback_type(lambda value, bias=bias: value + bias) for bias in range(300)]
for bias, callback in enumerate(callbacks):
    assert callback(42) == 42 + bias
maps = pathlib.Path('/proc/self/maps').read_text().splitlines()
assert not any('w' in line.split()[1] and 'x' in line.split()[1] for line in maps)
for callback in callbacks:
    address = C.cast(callback, C.c_void_p).value
    mappings = [line.split() for line in maps
                if int(line.split('-')[0], 16) <= address < int(line.split()[0].split('-')[1], 16)]
    assert len(mappings) == 1
    mapping = mappings[0]
    assert 'x' in mapping[1] and 'w' not in mapping[1] and '/libffi.so.' in mapping[-1], mapping
print(json.dumps({'passed': True, 'callbacks': len(callbacks),
                  'staticFileTrampolines': True, 'rwxRefused': True}))
