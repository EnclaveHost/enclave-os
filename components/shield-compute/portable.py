#!/usr/bin/env python3
"""Retain x86 SIMD dispatch; use the existing scalar implementation on RV64."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'Makefile';s=p.read_text()
s=s.replace('CORE_SRC :=', 'TARGET_MACHINE := $(shell $(CC) -dumpmachine)\nifneq (,$(findstring x86_64,$(TARGET_MACHINE)))\nSIMD_OBJ := shielded-simd-avx512.o\nendif\n\nCORE_SRC :=',1)
s=s.replace('$(CORE_SRC:.c=.o) shielded-simd-avx512.o', '$(CORE_SRC:.c=.o) $(SIMD_OBJ)')
s=s.replace('$(CORE_SRC:.c=.dealer.o) shielded-simd-avx512.o', '$(CORE_SRC:.c=.dealer.o) $(SIMD_OBJ)')
p.write_text(s)
p=root/'shielded-tee.c';s=p.read_text().replace('#if !defined(__aarch64__)', '#if defined(__x86_64__)')
needle='#else\n    bool want_avx512'
assert s.count(needle)==1
s=s.replace(needle, '#elif defined(__x86_64__)\n    bool want_avx512')
needle='    chosen = want_avx512 ? fast : &simd_generic;\n    return chosen;\n#endif'
assert s.count(needle)==1
s=s.replace(needle, '    chosen = want_avx512 ? fast : &simd_generic;\n    return chosen;\n#else\n    chosen = &simd_generic;\n    return chosen;\n#endif')
p.write_text(s)
