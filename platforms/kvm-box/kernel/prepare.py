#!/usr/bin/env python3
"""Rebuild the existing adapter ABI from a clean, pinned upstream kernel tree."""
import hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]).resolve()
source=pathlib.Path(__file__).resolve().parent
commit='427645e3db3a8896714f22a3d3fe0c3f7b317ad4'
assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==commit
pins={'recovered.config':'e033926581cd8488fccb0cee8c39a4408901fb3bc58d2f212c7977292d8bb59a',
      'enclave_openhcl_tpm.c':'c9bde9f889869a79543f69e21eaddcc78290eee9a16514e91252b73a4b131c56'}
for name,digest in pins.items():assert hashlib.sha256((source/name).read_bytes()).hexdigest()==digest
(root/'.config').write_bytes((source/'recovered.config').read_bytes())
tpm=root/'drivers/char/tpm'
assert not (tpm/'enclave_openhcl_tpm.c').exists()
(tpm/'enclave_openhcl_tpm.c').write_bytes((source/'enclave_openhcl_tpm.c').read_bytes())
with (tpm/'Kconfig').open('a') as f:
    f.write('\nconfig TCG_ENCLAVE_OPENHCL\n\tbool "Enclave OpenHCL guest TPM transport"\n\tdepends on TCG_TPM && X86_64 && HYPERV\n')
with (tpm/'Makefile').open('a') as f:f.write('\nobj-$(CONFIG_TCG_ENCLAVE_OPENHCL) += enclave_openhcl_tpm.o\n')
# Debug sections are not runtime features. The archived original configuration
# stays byte-for-byte pinned, and the actual resulting config is published too.
subprocess.run([str(root/'scripts/config'),'--file',str(root/'.config'),
                '--disable','DEBUG_INFO','--disable','DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT',
                '--disable','DEBUG_INFO_DWARF4','--disable','DEBUG_INFO_DWARF5',
                '--disable','DEBUG_INFO_BTF','--enable','DEBUG_INFO_NONE'],check=True)
subprocess.run(['make','olddefconfig'],cwd=root,check=True)
config=(root/'.config').read_text()
for feature in ['HYPERV','HYPERV_VSOCKETS','TCG_TPM','TCG_ENCLAVE_OPENHCL','EXT4_FS','SQUASHFS',
                'BLK_DEV_DM','DM_VERITY','SECCOMP_FILTER','INPUT_UINPUT','INPUT_EVDEV','UHID']:
    assert '\nCONFIG_'+feature+'=y\n' in config,feature
release=subprocess.check_output(['make','-s','kernelrelease'],cwd=root,text=True).strip()
assert release=='6.6.87.2-enclave-kvm-box',release
(root/'enclave-kernel-source.json').write_text(json.dumps({'repository':'microsoft/WSL2-Linux-Kernel',
    'commit':commit,'importedInputs':pins,'release':release,'fixtureOnly':True,
    'productionAdmission':False,'securityUpdateQualification':False,
    'configSha256':hashlib.sha256((root/'.config').read_bytes()).hexdigest()},indent=2)+'\n')
