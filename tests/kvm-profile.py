#!/usr/bin/env python3
import copy,importlib.util,json,pathlib,unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('profile',ROOT/'tools/kvm_profile.py')
profile=importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)

class Profile(unittest.TestCase):
    def setUp(self):
        self.kernel=json.loads((ROOT/'profiles/preview-kvm-kernel.json').read_text())
        self.retained=json.loads((ROOT/'profiles/preview-kvm-retained.json').read_text())
        self.image={'schema':'enclave-os-preview-root/1','userspaceVerityVerified':True,
            'corruptionRefused':{'rootfs.squashfs':True,'rootfs.verity':True},
            'image':{'file':'rootfs.squashfs','bytes':590233600,'sha256':'1'*64},
            'verity':{'file':'rootfs.verity','bytes':4653056,'dataBlocks':144100,
                'dataBlockSize':4096,'hashBlockSize':4096,'format':1,'hash':'sha256',
                'hashOffset':0,'superblock':False,'sha256':'2'*64,'rootHash':'3'*64,'salt':'4'*64}}

    def test_native_contract_geometry_and_canonical_encoding(self):
        raw=profile.generate(self.image,self.kernel,self.retained)
        parsed=json.loads(raw)
        self.assertEqual(raw,(json.dumps(parsed,sort_keys=True,separators=(',',':'))+'\n').encode())
        self.assertEqual(parsed['models'],self.retained['models'])
        self.assertEqual(parsed['kernel']['bootSha256'],self.kernel['files']['bzImage'])
        self.assertEqual(parsed['root']['hashBytes'],4653056)

    def test_unverified_or_incompatible_measurements_are_refused(self):
        changes=[lambda m:m.update(userspaceVerityVerified=False),
            lambda m:m['corruptionRefused'].update({'rootfs.verity':False}),
            lambda m:m['verity'].update(superblock=True),
            lambda m:m['image'].update(bytes=590233601),
            lambda m:m['verity'].update(bytes=4653057)]
        for change in changes:
            with self.subTest(change=change):
                mutated=copy.deepcopy(self.image);change(mutated)
                with self.assertRaises(ValueError):profile.generate(mutated,self.kernel,self.retained)

if __name__=='__main__':unittest.main()
