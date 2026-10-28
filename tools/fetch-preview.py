#!/usr/bin/env python3
"""Fetch identified CI package inputs, never a moving latest release."""
import argparse, hashlib, json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))

def main():
    parser = argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--browser-run', type=int)
    mode.add_argument('--preflight-without-browser', action='store_true',help='package composition test only; cannot produce a preview image')
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    inputs = json.loads((ROOT/'profiles/preview-x86-inputs.json').read_text())
    sources = inputs['sources']
    inputs['scope']='dependency-preflight-without-browser' if args.preflight_without_browser else 'preview'
    if not args.preflight_without_browser:
        sources.insert(0,{'name': 'browser', 'repository': 'EnclaveHost/enclave-browser',
                         'run': args.browser_run, 'packages': ['enclave-browser']})
    for source in sources:
        repo, run = source['repository'], source['run']
        info = api(f'repos/{repo}/actions/runs/{run}')
        # Some multi-architecture runs failed only on RV64. Require every
        # x86 job to succeed, rather than misclassifying the whole run.
        jobs = api(f'repos/{repo}/actions/runs/{run}/jobs?per_page=100')['jobs']
        relevant = [j for j in jobs if 'riscv' not in j['name'].lower()]
        if not relevant or any(j['conclusion'] != 'success' for j in relevant):
            raise ValueError(f'{repo} run {run}: x86 qualification has not passed')
        source['commit'] = info['head_sha']
        source['jobConclusions'] = {j['name']: j['conclusion'] for j in jobs}
        if source['name'] == 'browser':
            source['artifact'] = 'enclave-browser-alpine-' + info['head_sha']
        subprocess.run(['gh', 'run', 'download', str(run), '--repo', repo,
                        '--name', source['artifact'], '--dir', str(args.output/source['name'])], check=True)
        source['files'] = {str(p.relative_to(args.output/source['name'])):
                           hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
                           for p in sorted((args.output/source['name']).rglob('*')) if p.is_file()}
    (args.output/'inputs.json').write_text(json.dumps(inputs, indent=2)+'\n')

if __name__ == '__main__':
    main()
