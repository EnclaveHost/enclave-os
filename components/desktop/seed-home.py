#!/usr/bin/python3 -I
"""Install missing desktop defaults without replacing user files or permissions."""
import os
from pathlib import Path


def seed(source, home):
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    for item in sorted(source.rglob('*')):
        target = home / item.relative_to(source)
        if item.is_symlink():
            raise ValueError(f'Skeleton must contain regular files, not links: {item}')
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True, mode=0o700)
        elif item.is_file():
            # O_EXCL also preserves dangling symlinks instead of following them.
            try:
                fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            with os.fdopen(fd, 'wb') as output:
                output.write(item.read_bytes())


if __name__ == '__main__':
    seed(Path('/usr/share/enclave-os/skel'), Path.home())
