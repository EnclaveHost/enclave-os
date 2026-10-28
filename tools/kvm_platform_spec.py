"""Verify preview media and retained bootstrap bytes before platform compilation."""
import argparse, hashlib, json, pathlib, stat
from kvm_profile import generate
from kvm_media import iso

ROOT = pathlib.Path(__file__).resolve().parents[1]
RETAINED_MANIFEST = 'f8bcc7437e0c11d137b9de724f5245196a52af29baa3f592be62a1ea9d14b080'


def sha(path):
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('regular build input required: '+str(path))
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def verify_media(directory, profile, media):
    root = profile['root']
    expected = {'root.iso': (root['imageBytes'], root['imageSha256']),
                'hashes.iso': (root['hashBytes'], root['hashSha256'])}
    if set(media['files']) != set(expected):
        raise ValueError('missing native media')
    for name, (size, digest) in expected.items():
        record, path = media['files'][name], directory/name
        if (record['payloadBytes'], record['payloadSha256'], record['payloadOffset']) != (size, digest, 65536):
            raise ValueError('media/profile payload mismatch')
        if path.stat().st_size != size + 65536 or record['containerBytes'] != size + 65536:
            raise ValueError('media geometry mismatch')
        if sha(path) != record['containerSha256']:
            raise ValueError('media container hash mismatch')
        payload = hashlib.sha256()
        with path.open('rb') as stream:
            if stream.read(65536) != iso.header(size):
                raise ValueError('native optical header mismatch')
            while data := stream.read(1 << 20):
                payload.update(data)
        if payload.hexdigest() != digest:
            raise ValueError('media payload hash mismatch')


def prepare(preview, retained, output):
    preview, retained, output = (pathlib.Path(p).resolve() for p in (preview, retained, output))
    profile_path = preview/'kvm-profile.json'
    image = json.loads((preview/'image.json').read_text())
    kernel = json.loads((ROOT/'profiles/preview-kvm-kernel.json').read_text())
    expected = json.loads((ROOT/'profiles/preview-kvm-retained.json').read_text())
    if profile_path.read_bytes() != generate(image, kernel, expected):
        raise ValueError('profile differs from verified image and fixed kernel/controller/model pins')
    media = json.loads((preview/'kvm-media.json').read_text())
    if media['profileSha256'] != sha(profile_path):
        raise ValueError('media/profile mismatch')
    verify_media(preview, json.loads(profile_path.read_bytes()), media)
    for name in ('bzImage', 'vmlinux'):
        if sha(preview/'kvm-boot'/name) != kernel['files'][name]:
            raise ValueError('kernel export mismatch')
    manifest = retained/'inputs.json'
    if sha(manifest) != RETAINED_MANIFEST:
        raise ValueError('retained bootstrap manifest mismatch')
    entries = json.loads(manifest.read_text())['files']
    spec = {'schema': 'enclave-native-platform-build/1',
            'profile': {'path': str(profile_path), 'sha256': sha(profile_path)}, 'runtime': {}, 'storage': {}}
    for archive_path, record in entries.items():
        path = retained/record['file']
        if sha(path) != record['sha256'] or path.stat().st_size != record['bytes']:
            raise ValueError('retained bootstrap input mismatch: '+archive_path)
        group, name = ('runtime', archive_path[8:]) if archive_path.startswith('plat/rt/') else ('storage', archive_path)
        spec[group][name] = {'path': str(path), 'sha256': record['sha256']}
    with output.open('x') as f:
        json.dump(spec, f, indent=2); f.write('\n')
    return spec


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('preview'); p.add_argument('retained'); p.add_argument('output')
    a = p.parse_args(); prepare(a.preview, a.retained, a.output)
