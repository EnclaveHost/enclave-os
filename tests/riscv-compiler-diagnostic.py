#!/usr/bin/env python3
"""Observe the unchanged compiler limits on the two public Q8 reference kernels."""
import json,pathlib,subprocess,sys,time
sys.path.insert(0,'/src/components/shield-opencl')
from kernel_compiler import limits
from q8_kernel_compiler import CAPABILITIES,STRICT,REFERENCES

out=pathlib.Path('/out');results=[]
for name,file in REFERENCES.items():
    source=pathlib.Path('/src/components/shield-opencl/q8-reference')/file
    command=['/usr/bin/clang-18','-x','cl',*STRICT,*CAPABILITIES,
             '-fsyntax-only','-Xclang','-ast-dump=json',str(source)]
    started=time.monotonic()
    with (out/f'{name}.ast.json').open('wb') as ast,(out/f'{name}.stderr').open('wb') as errors:
        try:
            result=subprocess.run(command,stdout=ast,stderr=errors,timeout=15,preexec_fn=limits,
                                  env={'PATH':'/usr/bin:/bin','LANG':'C'})
            status=result.returncode
        except subprocess.TimeoutExpired:status='timeout'
    results.append({'variant':name,'status':status,'seconds':time.monotonic()-started,
                    'astBytes':(out/f'{name}.ast.json').stat().st_size,
                    'stderr':(out/f'{name}.stderr').read_text(errors='replace')[:8000]})
(out/'diagnostic.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
