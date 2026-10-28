"""Wrap measured preview payloads for the native launcher's fixed optical ABI."""
import hashlib, importlib.util, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_iso', ROOT/'reference/kvm-box/guest/native/build_iso.py')
iso = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iso)


def stage(directory):
    directory = pathlib.Path(directory)
    raw = (directory/'kvm-profile.json').read_bytes()
    profile = json.loads(raw)
    if profile['schema'] != 'enclave-native-desktop-profile/1':
        raise ValueError('requires native desktop profile')
    if raw != (json.dumps(profile, sort_keys=True, separators=(',', ':'))+'\n').encode():
        raise ValueError('noncanonical native profile')
    root = profile['root']
    pairs = [('rootfs.squashfs', 'root.iso', root['imageBytes'], root['imageSha256']),
             ('rootfs.verity', 'hashes.iso', root['hashBytes'], root['hashSha256'])]
    for source, target, size, digest in pairs:
        path = directory/source
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ValueError('invalid measured payload: '+source)
        if (directory/target).exists():
            raise ValueError('native media already exists: '+target)
    files = {}
    for source, target, size, digest in pairs:
        files[target] = iso.wrap(directory/source, directory/target, digest)
    report = {'schema': 'enclave-os-kvm-media/1', 'profileSha256': hashlib.sha256(raw).hexdigest(),
              'files': files, 'modelPayloadIncluded': False, 'controllerPayloadIncluded': False,
              'platformArchiveBuilt': False, 'runtimeAdmission': False, 'productionQualified': False}
    (directory/'kvm-media.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(stage(sys.argv[1])))
