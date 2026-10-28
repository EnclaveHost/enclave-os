#!/bin/sh
# Disposable remote CI only. Produces a userland candidate, not an admitted VM.
set -eux
apk add --no-cache python3 alpine-sdk sudo squashfs-tools cryptsetup
mkdir -p /out/repository/x86_64 /out/keys
python3 - <<'PY'
import hashlib,json,pathlib,re,shutil,subprocess
root=pathlib.Path('/inputs')
inputs=json.loads((root/'inputs.json').read_text())
assert inputs['scope']=='dependency-preflight-without-browser' if __import__('os').environ.get('ENCLAVE_PREVIEW_PREFLIGHT')=='1' else inputs['scope']=='preview'
selected={}
for source in inputs['sources']:
    directory=root/source['name']
    for key in directory.glob('*.pub'):
        target=pathlib.Path('/out/keys')/key.name
        if target.exists() and target.read_bytes()!=key.read_bytes():
            raise ValueError('signing key filename collision')
        shutil.copyfile(key,target)
        shutil.copyfile(key,pathlib.Path('/etc/apk/keys')/key.name)
    for package in source['packages']:
        files=[p for p in (directory/'repository/x86_64').glob('*.apk')
               if re.fullmatch(re.escape(package)+r'-[0-9][^-]*-r[0-9]+\.apk',p.name)]
        if len(files)!=1: raise ValueError((package,files))
        p=files[0]
        digest=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
        if digest!=source['files'][str(p.relative_to(directory))]:
            raise ValueError('artifact changed after fetch')
        subprocess.run(['apk','verify',str(p)],check=True)
        if package in selected: raise ValueError('duplicate package origin')
        selected[package]={'filename':p.name,'sha256':digest,'source':source['name']}
        shutil.copyfile(p,pathlib.Path('/out/repository/x86_64')/p.name)
pathlib.Path('/out/package-inputs.json').write_text(json.dumps(selected,indent=2)+'\n')
shutil.copyfile(root/'inputs.json','/out/build-inputs.json')
PY
adduser -D builder
addgroup builder abuild
su builder -c 'abuild-keygen -a -n'
cp /home/builder/.abuild/*.pub /out/keys/
# Match abuild's per-architecture repository layout, including noarch APKs.
# Without this, apk 3 tries to fetch those payloads from a nonexistent noarch/.
apk index --rewrite-arch x86_64 -o /out/repository/x86_64/APKINDEX.tar.gz /out/repository/x86_64/*.apk
abuild-sign -k /home/builder/.abuild/*.rsa /out/repository/x86_64/APKINDEX.tar.gz
if [ "${ENCLAVE_PREVIEW_PREFLIGHT:-0}" = 1 ]; then
    python3 /src/tools/preflight-preview.py
    exit
fi
set --
for key in /out/keys/*.pub; do set -- "$@" --key "$key"; done
python3 /src/tools/assemble.py --arch x86_64 --preset preview \
    --adapter kvm-box-native --repository /out/repository "$@" --output /out/root-preview
chroot /out/root-preview /bin/sh -ec '
    test "$(cat /etc/alpine-release)" = 3.24.3
    enclave-firefox --version
    python3 --version
    node --version
    for command in enclave-openarena enclave-librequake enclave-vpinball enclave-openhv enclave-sunshine llama-cli sd-cli; do
        command -v "$command"
    done
' >/out/root-startup.log 2>&1
mkdir -p /out/root-preview/etc/enclave-os
cp /out/root-preview.json /out/root-preview/etc/enclave-os/preview.json
printf '%s\n' 'Enclave OS preview: migration qualification incomplete; see /etc/enclave-os/preview.json.' >>/out/root-preview/etc/motd
# Image inputs contain no host identity or credentials. Remove privilege modes
# before making a read-only payload; role transitions belong to the adapter.
find /out/root-preview -type f -perm /6000 -exec chmod a-s '{}' +
mksquashfs /out/root-preview /out/rootfs.squashfs -noappend -comp xz -b 1M \
    -processors 2 -mem 512M -mkfs-time 0 -all-root -no-xattrs -no-progress >/out/squashfs.log
python3 /src/tools/measure-root.py /out/rootfs.squashfs /out/rootfs.verity > /out/image.json
sha256sum /out/rootfs.squashfs /out/rootfs.verity >/out/SHA256SUMS
rm -rf /out/root-preview
