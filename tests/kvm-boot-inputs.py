#!/usr/bin/env python3
import importlib.util,pathlib,tempfile,unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('boot',ROOT/'tools/kvm_boot_inputs.py')
boot=importlib.util.module_from_spec(spec);spec.loader.exec_module(boot)

class BootInputs(unittest.TestCase):
    def fixture(self,base):
        root=base/'root';root.mkdir();(root/'desktop.profile').write_bytes(b'KVM-BOX-MASKED/1\n')
        helpers=root/'usr/libexec/enclave-os/native';helpers.mkdir(parents=True)
        for name in ('nsinit','gateway','supervisor'):
            p=helpers/name;p.write_bytes(name.encode());p.chmod(0o555)
        kernel=base/'kernel';kernel.mkdir()
        for name in ('bzImage','vmlinux','nft_ct.ko','.config'):(kernel/name).write_bytes(name.encode())
        pin={'files':{p.name:boot.digest(p) for p in kernel.iterdir()}}
        return root,kernel,base/'export',pin

    def test_fixed_abi_contains_regular_identical_helpers_and_pinned_module(self):
        with tempfile.TemporaryDirectory() as temp:
            root,kernel,out,pin=self.fixture(pathlib.Path(temp))
            report=boot.stage(root,kernel,out,pin=pin)
            for name in boot.HELPERS:
                old=root/'usr/local/libexec/kvm-box'/name
                new=root/'usr/libexec/enclave-os/native'/name
                self.assertFalse(old.is_symlink());self.assertTrue(old.samefile(new))
            self.assertEqual((root/'usr/local/libexec/kvm-box/nft_ct.ko').read_bytes(),b'nft_ct.ko')
            self.assertEqual(report['exports']['supervisor'],boot.digest(out/'supervisor'))
            self.assertFalse(report['runtimeAdmission'])

    def test_changed_kernel_refused_before_root_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root,kernel,out,pin=self.fixture(pathlib.Path(temp))
            (kernel/'nft_ct.ko').write_bytes(b'wrong kernel module')
            with self.assertRaisesRegex(ValueError,'kernel hash mismatch'):
                boot.stage(root,kernel,out,pin=pin)
            self.assertFalse((root/'usr/local').exists());self.assertFalse(out.exists())

    def test_symlink_destination_refused_before_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root,kernel,out,pin=self.fixture(pathlib.Path(temp))
            (root/'usr/local').symlink_to(kernel,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlink in KVM boot path'):
                boot.stage(root,kernel,out,pin=pin)
            self.assertFalse(out.exists());self.assertFalse((kernel/'libexec').exists())

if __name__=='__main__':unittest.main()
