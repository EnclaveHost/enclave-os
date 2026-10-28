#!/usr/bin/env python3
"""Apply the recovered standard-API app patches to the verified SDK export."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

here = Path(__file__).resolve().parent
out = Path(sys.argv[1]).resolve()
provenance = json.loads((out / 'source-provenance.json').read_text())
patches = {
    'llama': ['llama-desktop-loopback.patch', 'llama-shield-opencl.patch',
              'llama-shield-cpu-fallback.patch', 'llama-opencl-q8-views.patch',
              'llama-shield-source-cache.patch'],
    'sd': ['sd-opencl-fallback.patch', 'sd-opencl-graph-operations.patch',
           'sd-opencl-upload.patch', 'sd-graph-diagnostic.patch', 'sd-opencl-capabilities.patch'],
}
for tree, names in patches.items():
    for name in names:
        patch = here / name
        subprocess.run(['git', 'apply', str(patch)], cwd=out / tree, check=True)
        provenance['archiveAndPatchSha256'][name] = hashlib.sha256(patch.read_bytes()).hexdigest()
shutil.copyfile(here / 'build-standard.sh', out / 'build.sh')
provenance['variant'] = 'standard-opencl-apps; separate from trusted service SDK'
for name in ('prepare-standard.py', 'build-standard.sh'):
    provenance['recipeSha256'][name] = hashlib.sha256((here / name).read_bytes()).hexdigest()
(out / 'source-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
