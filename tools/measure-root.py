#!/usr/bin/env python3
"""Create and corruption-test a dm-verity sidecar, without mapping devices."""
import hashlib,json,os,pathlib,re,subprocess,sys
image,sidecar=map(pathlib.Path,sys.argv[1:])
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
size=image.stat().st_size
assert size>0 and size%4096==0
digest=sha(image)
salt=hashlib.sha256(b'kvm-box-native-root-verity/1\0'+bytes.fromhex(digest)).hexdigest()
sidecar.touch(exist_ok=False)
options=['--no-superblock','--format=1','--hash=sha256','--hash-offset=0',
         '--data-block-size=4096','--hash-block-size=4096',f'--data-blocks={size//4096}',f'--salt={salt}']
env={**os.environ,'LC_ALL':'C'}
result=subprocess.run(['veritysetup','format',*options,str(image),str(sidecar)],check=True,capture_output=True,text=True,env=env)
roots=re.findall(r'^Root hash:\s*([0-9a-f]{64})\s*$',result.stdout,re.M)
assert len(roots)==1
verify=['veritysetup','verify',*options,str(image),str(sidecar),roots[0]]
subprocess.run(verify,check=True,capture_output=True,env=env)
negative={}
for path in (image,sidecar):
    before=sha(path)
    with path.open('r+b') as f:
        original=f.read(1);f.seek(0);f.write(bytes([original[0]^1]));f.flush();os.fsync(f.fileno())
        try:
            negative[path.name]=subprocess.run(verify,capture_output=True,env=env,timeout=120).returncode!=0
        finally:
            f.seek(0);f.write(original);f.flush();os.fsync(f.fileno())
    assert negative[path.name] and sha(path)==before
subprocess.run(verify,check=True,capture_output=True,env=env)
print(json.dumps({'schema':'enclave-os-preview-root/1','architecture':'x86_64',
    'image':{'file':image.name,'sha256':digest,'bytes':size,'filesystem':'squashfs','compression':'xz'},
    'verity':{'file':sidecar.name,'sha256':sha(sidecar),'bytes':sidecar.stat().st_size,
              'rootHash':roots[0],'salt':salt,'dataBlocks':size//4096,'dataBlockSize':4096,
              'hashBlockSize':4096,'format':1,'hash':'sha256','hashOffset':0,'superblock':False},
    'userspaceVerityVerified':True,'corruptionRefused':negative,
    'runtimeAdmission':False,'productionQualified':False},indent=2))
