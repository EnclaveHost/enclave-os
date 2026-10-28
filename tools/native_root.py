"""Finish a newly assembled native payload; never operate on a running root."""
import json,pathlib,shutil

EMPTY={
    'home':0o755,'home/desktop':0o700,'root':0o700,'run':0o755,
    'tmp':0o1777,'var/tmp':0o1777,'var/log':0o755,'var/backups':0o755,
    'var/mail':0o755,'var/spool':0o755,'var/lib/private':0o700,
    'var/cache/private':0o700,'dev':0o755,'proc':0o755,'sys':0o755,
    'models':0o755,'etc/udev/rules.d':0o755,'usr/lib/udev/rules.d':0o755,
}

def configure(root,rules):
    root=pathlib.Path(root).resolve()
    if root==pathlib.Path('/') or (root/'desktop.profile').read_bytes()!=b'KVM-BOX-MASKED/1\n':
        raise ValueError('requires a separately assembled native payload')
    def target(relative):
        p=root/relative
        for parent in (p,*p.parents):
            if parent==root:break
            if parent.is_symlink():raise ValueError('symlink in native configuration path: '+relative)
        return p
    # Validate every path before removing any package-created runtime state.
    files=('etc/machine-id','var/lib/dbus/machine-id','etc/hostname','etc/hosts',
           'etc/resolv.conf','usr/lib/enclave-browser/distribution/policies.json')
    for relative in (*EMPTY,*files):target(relative)
    policy_path=target(files[-1]);policies=json.loads(policy_path.read_text())
    removed_rules=sorted(str(p.relative_to(root)) for name in ('etc/udev/rules.d','usr/lib/udev/rules.d')
                         for p in target(name).rglob('*') if p.is_file() or p.is_symlink())
    for relative,mode in EMPTY.items():
        p=target(relative)
        if p.exists():
            if not p.is_dir():raise ValueError('expected native mountpoint directory: '+relative)
            shutil.rmtree(p)
        p.mkdir(parents=True);p.chmod(mode)
    p=target('usr/lib/udev/rules.d/70-kvm-box-input.rules');p.write_bytes(rules);p.chmod(0o444)
    # Public image identity from the recovered adapter, never a builder identity.
    for relative in ('etc/machine-id','var/lib/dbus/machine-id'):
        p=target(relative);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('7a25482197b340dfb14a17300cbbdd73\n')
    target('etc/hostname').write_text('kvm-box\n')
    target('etc/hosts').write_text('127.0.0.1 localhost\n::1 localhost ip6-localhost ip6-loopback\n127.0.1.1 kvm-box\n')
    target('etc/resolv.conf').write_text('nameserver 127.0.0.2\noptions timeout:2 attempts:2\n')
    policies['policies']['Proxy']={'Mode':'manual','Locked':True,
        'SOCKSProxy':'127.0.0.2:1080','SOCKSVersion':5,'UseProxyForDNS':True,'Passthrough':''}
    policy_path.write_text(json.dumps(policies,indent=2)+'\n')
    return {'emptySessionMountpoints':list(EMPTY),'replacedUdevRules':removed_rules,
            'inputRules':'70-kvm-box-input.rules','browserProxy':'127.0.0.2:1080'}
