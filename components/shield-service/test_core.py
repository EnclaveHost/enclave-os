"""Compare compiled core helpers to the pinned independent Python field reference."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
import numpy as np

spec = importlib.util.spec_from_file_location('field_reference', 'upstream/shielded/field.py')
field = importlib.util.module_from_spec(spec)
spec.loader.exec_module(field)


def run(name, data='', *args):
    return subprocess.check_output([str(Path('core').resolve() / name), *args],
                                   input=data, text=True, timeout=60)


class CoreNumerics(unittest.TestCase):
    def test_constants(self):
        actual = json.loads(run('field-selftest', '', '--constants'))
        expected = dict(M_MOD=field.M_MOD, HALF_M=field.HALF_M, primes=list(field.PRIMES),
                        QK=field.QK, FRAC=field.FRAC, WEIGHT_BYTE_LIMIT=field.WEIGHT_BYTE_LIMIT)
        self.assertEqual(actual, expected)

    def test_cross_language_encoding(self):
        vectors = field.encoding_vectors(n=4096)
        data = ''.join(f'{h} {q}\n' for h, q in zip(vectors['half_bits'], vectors['quant']))
        self.assertEqual(list(map(int, run('field-selftest', data).split())), vectors['w_fixed'])

    def test_half_rounding(self):
        rng = np.random.default_rng(71)
        values = np.concatenate((rng.uniform(-65000, 65000, 4096),
            [0, -0., 2**-24, 2**-25, -2**-24, 2**-14, 1.00048828125, 1.00146484375])).astype(np.float32)
        expected = values.astype(np.float16).view(np.uint16).tolist()
        actual = list(map(int, run('half-selftest', '\n'.join(map(str, values)) + '\n').split()))
        self.assertEqual(actual, expected)

    def test_preparation_known_power_of_two_exponents(self):
        # Independent exact cases: zero column, unit weight, double, lane limit.
        quants = ' '.join(map(str, [0, 1, 2, 119] * 32))
        self.assertEqual(list(map(int, run('prepare-selftest', '32 4\n15360 15360 15360 15360\n' + quants + '\n').split())), [8, 6, 5, 0])
