"""Stage the existing KVM launcher's fixed ABI into a separate preview root."""
import hashlib,json,pathlib,shutil,stat

ROOT=pathlib.Path(__file__).resolve().parents[1]
HELPERS=('nsinit','gateway','supervisor')

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def stage(root,kernel,output,*,pin=None):
    root,kernel,output=map(pathlib.Path,(root,kernel,output))
    root=root.resolve()
    if root==pathlib.Path('/') or (root/'desktop.profile').read_bytes()!=b'KVM-BOX-MASKED/1\n':
        raise ValueError('requires separately assembled native root')
    if output.exists():raise ValueError('KVM export must not exist')
    pin=pin or json.loads((ROOT/'profiles/preview-kvm-kernel.json').read_text())
    for name,expected in pin['files'].items():
        p=kernel/name
        if p.is_symlink() or not p.is_file() or digest(p)!=expected:
            raise ValueError('kernel hash mismatch: '+name)
    def target(relative):
        p=root/relative
        for parent in (p,*p.parents):
            if parent==root:break
            if parent.is_symlink():raise ValueError('symlink in KVM boot path: '+relative)
        return p
    canonical=target('usr/libexec/enclave-os/native')
    legacy=target('usr/local/libexec/kvm-box')
    for name in HELPERS:
        p=target('usr/libexec/enclave-os/native/'+name)
        if not p.is_file() or stat.S_IMODE(p.stat().st_mode)!=0o555:
            raise ValueError('missing or writable native helper: '+name)
    for name in (*HELPERS,'nft_ct.ko'):
        if (legacy/name).exists() or (legacy/name).is_symlink():
            raise ValueError('KVM boot destination already exists: '+name)
    # O_NOFOLLOW/RESOLVE_NO_SYMLINKS are part of the deployed boot boundary.
    # Hard links preserve that ABI without a second executable payload.
    legacy.mkdir(parents=True,exist_ok=True)
    for name in HELPERS:(legacy/name).hardlink_to(canonical/name)
    shutil.copyfile(kernel/'nft_ct.ko',legacy/'nft_ct.ko')
    (legacy/'nft_ct.ko').chmod(0o444)
    output.mkdir(parents=True)
    for name in ('nsinit','supervisor','gateway'):
        shutil.copyfile(canonical/name,output/name);(output/name).chmod(0o555)
    for name in ('bzImage','vmlinux'):
        shutil.copyfile(kernel/name,output/name);(output/name).chmod(0o444)
    report={'schema':'enclave-os-kvm-boot-inputs/1','kernel':pin,
        'fixedRootPaths':{str((legacy/name).relative_to(root)):digest(legacy/name)
                          for name in (*HELPERS,'nft_ct.ko')},
        'exports':{p.name:digest(p) for p in sorted(output.iterdir())},
        'minimumMemoryMiB':8192,'platformArchiveBuilt':False,
        'runtimeAdmission':False,'productionQualified':False}
    (output/'inputs.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    import sys
    if len(sys.argv)!=4:raise SystemExit('usage: kvm_boot_inputs.py ROOT KERNEL EXPORT')
    stage(*sys.argv[1:])
