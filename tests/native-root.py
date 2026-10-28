#!/usr/bin/env python3
"""Exercise native image preparation without mounts or host state."""
import importlib.util,json,pathlib,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('native_root',ROOT/'tools/native_root.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class NativeRoot(unittest.TestCase):
    def fixture(self,root):
        (root/'desktop.profile').write_bytes(b'KVM-BOX-MASKED/1\n')
        for name in ('etc/udev/rules.d','usr/lib/udev/rules.d','home/desktop',
                     'var/log','usr/lib/enclave-browser/distribution'):
            (root/name).mkdir(parents=True,exist_ok=True)
        (root/'usr/lib/udev/rules.d/50-unwanted.rules').write_text('RUN+="helper"\n')
        (root/'home/desktop/builder-state').write_text('discard')
        (root/'usr/lib/enclave-browser/distribution/policies.json').write_bytes(
            (ROOT/'components/desktop/browser/policies.json').read_bytes())

    def test_closed_rules_fresh_session_and_preserved_browser_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);self.fixture(root)
            rules=(ROOT/'components/native-platform/70-kvm-box-input.rules').read_bytes()
            mod.configure(root,rules)
            self.assertEqual(list((root/'home/desktop').iterdir()),[])
            self.assertEqual((root/'home/desktop').stat().st_mode&0o777,0o700)
            self.assertEqual([p.name for p in (root/'usr/lib/udev/rules.d').iterdir()],['70-kvm-box-input.rules'])
            self.assertEqual((root/'usr/lib/udev/rules.d/70-kvm-box-input.rules').read_bytes(),rules)
            p=json.loads((root/'usr/lib/enclave-browser/distribution/policies.json').read_text())['policies']
            self.assertIn('uBlock0@raymondhill.net',p['ExtensionSettings'])
            self.assertEqual(p['Proxy']['SOCKSProxy'],'127.0.0.2:1080')
            self.assertTrue(p['Proxy']['Locked'])

    def test_symlink_rejected_before_runtime_state_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp,tempfile.TemporaryDirectory() as other:
            root=pathlib.Path(tmp);self.fixture(root)
            (root/'etc/resolv.conf').symlink_to(pathlib.Path(other)/'resolv.conf')
            with self.assertRaisesRegex(ValueError,'symlink'):mod.configure(root,b'rules')
            self.assertTrue((root/'home/desktop/builder-state').exists())
            self.assertFalse((pathlib.Path(other)/'resolv.conf').exists())

if __name__=='__main__':unittest.main()
