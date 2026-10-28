"""Bind the separate measured preview to the retained native profile ABI."""
import hashlib,json,pathlib,sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def tree_bytes(blocks):
    total=0
    while blocks>1:
        blocks=(blocks+127)//128
        total+=blocks*4096
    return total

def generate(image,kernel,retained):
    if image['schema']!='enclave-os-preview-root/1' or image['userspaceVerityVerified'] is not True:
        raise ValueError('requires verified measured preview')
    data,v=image['image'],image['verity']
    if image['corruptionRefused']!={data['file']:True,v['file']:True}:
        raise ValueError('requires both corruption refusal checks')
    if (v['dataBlockSize'],v['hashBlockSize'],v['format'],v['hash'],v['hashOffset'],v['superblock'])!=(4096,4096,1,'sha256',0,False):
        raise ValueError('unsupported native verity format')
    if not 2<=v['dataBlocks']<=(8<<30)//4096 or data['bytes']!=v['dataBlocks']*4096 or v['bytes']!=tree_bytes(v['dataBlocks']):
        raise ValueError('invalid native root geometry')
    models=retained['models']
    if models['hashStartBlock']!=models['dataBlocks']+1 or models['imageBytes']!=models['hashStartBlock']*4096+tree_bytes(models['dataBlocks']):
        raise ValueError('invalid retained model geometry')
    if len({data['bytes'],v['bytes'],models['imageBytes']})!=3:
        raise ValueError('native media sizes must differ')
    profile={'schema':'enclave-native-desktop-profile/1','profile':'kvm-box-masked-v1',
        'controllerSha256':retained['controllerSha256'],
        'kernel':{'release':kernel['release'],'bootSha256':kernel['files']['bzImage'],
                  'elfSha256':kernel['files']['vmlinux']},
        'models':models,
        'root':{'dataBlocks':v['dataBlocks'],'hashBytes':v['bytes'],'hashSha256':v['sha256'],
                'imageBytes':data['bytes'],'imageSha256':data['sha256'],
                'rootHash':v['rootHash'],'salt':v['salt']}}
    return (json.dumps(profile,sort_keys=True,separators=(',',':'))+'\n').encode()

def main(directory):
    directory=pathlib.Path(directory)
    image=json.loads((directory/'image.json').read_text())
    kernel=json.loads((ROOT/'profiles/preview-kvm-kernel.json').read_text())
    retained=json.loads((ROOT/'profiles/preview-kvm-retained.json').read_text())
    raw=generate(image,kernel,retained)
    with (directory/'kvm-profile.json').open('xb') as f:f.write(raw)
    (directory/'kvm-preview-status.json').write_text(json.dumps({
        'profileSha256':hashlib.sha256(raw).hexdigest(),'modelPayloadIncluded':False,
        'controllerPayloadIncluded':False,'platformArchiveBuilt':False,
        'runtimeAdmission':False,'productionQualified':False},indent=2)+'\n')

if __name__=='__main__':main(sys.argv[1])
