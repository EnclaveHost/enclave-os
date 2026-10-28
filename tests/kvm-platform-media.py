import hashlib, json, pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from kvm_platform_spec import verify_media
from kvm_media import iso

class Media(unittest.TestCase):
    def test_payload_binding_survives_recomputed_container_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            profile = {'root': {}}
            files = {}
            for name, prefix, data in [('root.iso', 'image', b'r'*8192), ('hashes.iso', 'hash', b'h'*4096)]:
                digest = hashlib.sha256(data).hexdigest()
                profile['root'].update({prefix+'Bytes': len(data), prefix+'Sha256': digest})
                source = root/(name+'.raw'); source.write_bytes(data)
                files[name] = iso.wrap(source, root/name, digest)
            media = {'files': files}
            verify_media(root, profile, media)
            path = root/'root.iso'; path.chmod(0o644)
            original = path.read_bytes()
            for index, error in [(65536, 'payload hash mismatch'), (0, 'header mismatch')]:
                with self.subTest(index=index):
                    changed = bytearray(original); changed[index] ^= 1; path.write_bytes(changed)
                    files['root.iso']['containerSha256'] = hashlib.sha256(changed).hexdigest()
                    with self.assertRaisesRegex(ValueError, error): verify_media(root, profile, media)
            path.write_bytes(original)
            files['root.iso']['containerSha256'] = hashlib.sha256(original).hexdigest()
            files['root.iso']['payloadOffset'] = 0
            with self.assertRaisesRegex(ValueError, 'payload mismatch'): verify_media(root, profile, media)

if __name__ == '__main__': unittest.main()
