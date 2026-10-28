"""Reproduce the retained IGVM recipe, then bind the Alpine native platform.

Produces an unsigned candidate and an explicitly rejected debug twin. This does
not grant host admission, sign an image, or change any production configuration.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(path):
    return json.loads(path.read_text())['series'][0]['reference']['vbs_boot_digest']


def elf_load_middle(data):
    if data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('expected little endian ELF64')
    offset, = struct.unpack_from('<Q', data, 32)
    size, count = struct.unpack_from('<HH', data, 54)
    for i in range(count):
        at = offset + i * size
        kind, = struct.unpack_from('<I', data, at)
        start, = struct.unpack_from('<Q', data, at + 8)
        length, = struct.unpack_from('<Q', data, at + 32)
        if kind == 1 and length:
            middle = start + length // 2
            if middle >= len(data):
                raise ValueError('ELF segment exceeds input')
            return middle
    raise ValueError('no loadable ELF segment')


def build(inputs, platform, preview, output, fixture=None):
    inputs, platform, preview, output = [pathlib.Path(p).resolve() for p in (inputs, platform, preview, output)]
    lock = json.loads((ROOT/'profiles/kvm-firmware-inputs.json').read_text())
    recipe = lock['recipe']
    for name, record in lock['files'].items():
        path = inputs/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != record['bytes'] or sha(path) != record['sha256']:
            raise ValueError('retained firmware input mismatch: '+name)
    tool = inputs/recipe['igvmfilegen']
    tool.chmod(0o755)
    receipt = json.loads((platform/'platform/build.json').read_text())
    initrd = platform/'platform/native.cpio.gz'
    kernel = preview/'kvm-boot/vmlinux'
    kernel_pin = json.loads((ROOT/'profiles/preview-kvm-kernel.json').read_text())['files']['vmlinux']
    if sha(initrd) != receipt['initrd']['sha256'] or sha(kernel) != kernel_pin:
        raise ValueError('native platform or kernel mismatch')
    profile_sha = sha(preview/'kvm-profile.json')
    if profile_sha != receipt['inputPins']['profile']['sha256']:
        raise ValueError('native platform belongs to another preview')
    archive_check = json.loads((platform/'platform/archive-check.json').read_text())
    if archive_check.get('passed') is not True or archive_check.get('initrdSha256') != sha(initrd):
        raise ValueError('native archive qualification required')
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='igvm-', dir=output) as tmp:
        temp = pathlib.Path(tmp)

        def run(name, manifest, resources, overrides=None, args=(), keep=False):
            directory = temp/name
            directory.mkdir()
            paths = {key: str(inputs/value) for key, value in resources.items()}
            for key, value in (overrides or {}).items():
                if isinstance(value, pathlib.Path):
                    paths[key] = str(value)
                else:
                    path = directory/key
                    path.write_bytes(value)
                    paths[key] = str(path)
            mpath, rpath = directory/'manifest.json', directory/'resources.json'
            mpath.write_bytes(manifest)
            rpath.write_text(json.dumps({'resources': paths}))
            binary, vbs = directory/'image.bin', directory/'image-vbs.json'
            subprocess.run([str(tool), 'manifest', '-m', str(mpath), '-r', str(rpath), '-o', str(binary), *args], check=True, timeout=180)
            result = {'sha256': sha(binary), 'bytes': binary.stat().st_size,
                      'vbsSha256': sha(vbs), 'measurement': digest(vbs)}
            if keep:
                shutil.copyfile(binary, output/(name+'.bin'))
                shutil.copyfile(vbs, output/(name+'-vbs.json'))
            shutil.rmtree(directory)
            return result

        manifest = (inputs/recipe['manifest']).read_bytes()
        baseline = run('baseline', manifest, recipe['resources'])
        if baseline['sha256'] != lock['expectedBaselineSha256'] or baseline['measurement'] != digest(inputs/recipe['vbsJson']):
            raise ValueError('retained firmware recipe no longer reproduces')
        twin = recipe['twin']
        proof = run('twin-proof', (inputs/twin['manifest']).read_bytes(), twin['resources'])
        if proof['measurement'] != digest(inputs/twin['expectVbsJson']):
            raise ValueError('retained twin proof differs')
        if fixture is not None:
            fixture = pathlib.Path(fixture).resolve()
            fixture_record = json.loads((fixture/'fixture.json').read_text())
            if fixture_record['productionInitrdSha256'] != sha(initrd) or fixture_record['profileSha256'] != profile_sha:
                raise ValueError('fixture does not extend this production platform')
            initrd = fixture/'probe.cpio.gz'
            if sha(initrd) != fixture_record['initrdSha256']:
                raise ValueError('fixture archive mismatch')
            document = json.loads(manifest)
            document['guest_configs'][0]['image']['openhcl']['linux']['command_line'] = (
                'console=ttyS0 rdinit=/probe-init loglevel=4 report_host=9001 native.monitor.probe=1 native.startup.probe=1')
            manifest = json.dumps(document).encode()
            lock['requiredStrings'] = ['OPENHCL_FORCE_LOAD_VTL0_IMAGE=linux',
                                       'rdinit=/probe-init', 'native.monitor.probe=1']
        overrides = {'linux_initrd': initrd, 'linux_kernel': kernel,
                     'underhill_initrd': inputs/'openhcl-shield.cpio.gz'}
        candidate = run('candidate', manifest, recipe['resources'], overrides, keep=True)
        repeated = run('candidate-again', manifest, recipe['resources'], overrides)
        if candidate != repeated:
            raise ValueError('firmware is not deterministic')
        binary = (output/'candidate.bin').read_bytes()
        if any(s.encode() not in binary for s in lock['requiredStrings']) or any(s.encode() in binary for s in lock['forbiddenStrings']):
            raise ValueError('candidate command line differs')
        debug = run('DEBUG-TRUSTS-HOST-REFUSE', manifest, recipe['resources'], overrides, lock['debugArgs'], keep=True)
        if debug['measurement'] == candidate['measurement']:
            raise ValueError('debug twin shares candidate measurement')
        mutations = []
        for index, mutation in enumerate(recipe['mutations']):
            modified, resources = manifest, dict(overrides)
            if mutation['kind'] == 'resourceByte':
                key = mutation['resource']
                data = bytearray(resources.get(key, inputs/recipe['resources'][key]).read_bytes())
                at = elf_load_middle(data) if mutation['at'] == 'elfFirstLoadMiddle' else len(data)//2
                data[at] ^= 1
                resources[key] = data
            elif mutation['kind'] == 'manifestEdit':
                document = json.loads(manifest)
                leaf = document
                for key in mutation['path'][:-1]:
                    leaf = leaf[key]
                key = mutation['path'][-1]
                leaf[key] = str(leaf[key])+mutation['append'] if 'append' in mutation else mutation['set']
                modified = json.dumps(document).encode()
            else:
                raise ValueError('unknown mutation')
            result = run('mutation-'+str(index), modified, recipe['resources'], resources)
            if result['measurement'] == candidate['measurement']:
                raise ValueError('mutation did not change measurement: '+mutation['name'])
            mutations.append({'name': mutation['name'], 'measurement': result['measurement'], 'changed': True})
    record = {'schema': 'enclave-os-native-firmware-candidate/1', 'baseline': baseline,
              'twinProof': proof, 'candidate': candidate, 'deterministic': True,
              'debugTwinRefused': debug, 'mutations': mutations, 'profileSha256': profile_sha,
              'inputs': {'initrdSha256': sha(initrd), 'kernelSha256': sha(kernel),
                         'retainedArchiveSha256': lock['archiveSha256']},
              'signed': False, 'admitted': False, 'fullServiceStartup': False}
    if fixture is not None:
        record['disposableFixtureOnly'] = True
        record['fixture'] = fixture_record
    (output/'build.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'platform', 'preview', 'output'):
        parser.add_argument(name)
    parser.add_argument('--fixture', help='Explicit disposable service-test archive; never a serving image')
    args = parser.parse_args()
    build(args.inputs, args.platform, args.preview, args.output, args.fixture)
