"""Minimal runtime mounts for a disposable CI root, never a host/VM launcher."""
import contextlib,os,pathlib,stat,subprocess,sys

@contextlib.contextmanager
def runtime(root):
    root=pathlib.Path(root).resolve()
    proc=root/'proc';proc.mkdir(exist_ok=True)
    dev=root/'dev';dev.mkdir(exist_ok=True)
    created=[]
    mounts=[]
    try:
        for name,minor in (('null',3),('zero',5),('random',8),('urandom',9)):
            path=dev/name
            if path.exists() or path.is_symlink():
                info=path.lstat()
                if not stat.S_ISCHR(info.st_mode) or info.st_rdev!=os.makedev(1,minor):
                    raise ValueError('unexpected runtime device: '+str(path))
            else:
                os.mknod(path,stat.S_IFCHR|0o666,os.makedev(1,minor));created.append(path)
                path.chmod(0o666)
        # musl resolves $ORIGIN for the main executable through /proc/self/exe.
        # This is the disposable container's PID namespace, not the host's.
        for name in ('proc','sys'):
            target=root/name;target.mkdir(exist_ok=True)
            fs='sysfs' if name=='sys' else 'proc'
            subprocess.run(['mount','-t',fs,'-o','ro,nosuid,nodev,noexec',fs,str(target)],check=True)
            mounts.append(target)
        yield
    finally:
        for target in reversed(mounts):subprocess.run(['umount',str(target)],check=True)
        for path in created:path.unlink()

if __name__=='__main__':
    with runtime(sys.argv[1]):
        subprocess.run(['chroot',sys.argv[1],*sys.argv[2:]],check=True,timeout=120)
