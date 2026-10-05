import json, glob, os, re
def texts(n, out):
    if isinstance(n, dict):
        a = n.get('attributes', {})
        for k in ('text', 'accessibilityText', 'hintText'):
            v = a.get(k)
            if v: out.extend(s for s in v.split('\n') if s)
        for c in n.get('children', []): texts(c, out)
for run in ('m211ja', 'm211ar'):
    for d in sorted(glob.glob(f'debug-{run}/.maestro/tests/*/a2-{run}-*')):
        flow = os.path.basename(d)
        cmds = json.load(open(f'{d}/commands.json'))
        os.makedirs(f'results/{run}', exist_ok=True); shot = None
        for e in cmds:
            cmd = e['command']; k = next(iter(cmd)); m = e['metadata']
            lab = (cmd[k] or {}).get('label') if isinstance(cmd[k], dict) else None
            if lab and lab.startswith('shotfleet:hier:'):
                name = lab.split(':')[-1]
                h = next(a['path'] for a in m['artifacts'] if a['type'] == 'SCREEN_HIERARCHY')
                out = []; texts(json.load(open(f'{d}/{h}')), out)
                keep = [s for s in dict.fromkeys(out) if not re.search(r'^\d{1,2}:\d\d|notification|bars|Battery|5G|signal|T-Mobile|PM$|AM$', s)]
                open(f'results/{run}/{flow}-{name}.txt', 'w').write('\n'.join(keep) + '\n')
                print(run, flow, name, round(m['duration']), 'ms', '|', ' / '.join(keep))
