#!/usr/bin/env python3
"""Exercise the installed isolated compiler, including its packaged reference data."""
import json
from pathlib import Path
import subprocess

compiler = '/usr/lib/enclave-shield-opencl/q8_capture_compiler.py'
reference = Path('/src/components/shield-opencl/q8-reference')
for variant, filename, name, before, after in (
    ('mm', 'mul_mm_q8_0_f32_l4_lm.cl', 'kernel_mul_mm_q8_0_f32_l4_lm', 'block < ne00', 'block <= ne00'),
    ('mv', 'mul_mv_q8_0_f32_flat.cl', 'kernel_mul_mv_q8_0_f32_flat', 'sumq += qv.s0*yl.s0', 'sumq -= qv.s0*yl.s0'),
):
    source = (reference/filename).read_text()
    assert before in source
    def compile(text):
        result = subprocess.run(['python3', '-I', compiler],
            input=json.dumps({'source':text,'options':'-cl-std=CL3.0'}),
            capture_output=True, text=True, check=True, timeout=30)
        return json.loads(result.stdout)
    plan = compile(source)[name]
    assert plan['variant'] == variant and plan['dispatchable'] is False
    assert 'authenticated-public-q8-tensor' in plan['requires']
    assert compile(source.replace(before, after)) == {}
    print('PASS: installed',variant,'typed recognition, admission requirement and changed-arithmetic rejection')
