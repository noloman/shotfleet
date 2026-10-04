import json, sys, glob, os
def texts(n, out):
    if isinstance(n, dict):
        a = n.get('attributes', {})
        for k in ('text', 'accessibilityText', 'hintText'):
            v = a.get(k)
            if v:
                out.extend(s for s in v.split('\n') if s)
        for c in n.get('children', []): texts(c, out)
for run in ('control', 'probe'):
    d = glob.glob(f'debug-{run}/.maestro/tests/*/expA-{run}')[0]
    cmds = json.load(open(f'{d}/commands.json'))
    os.makedirs(f'results/{run}', exist_ok=True)
    shot = None
    for e in cmds:
        cmd = e['command']; k = next(iter(cmd)); m = e['metadata']
        if k == 'takeScreenshotCommand':
            shot = os.path.basename(cmd[k]['path'])
        lab = (cmd[k] or {}).get('label') if isinstance(cmd[k], dict) else None
        if lab and lab.startswith('shotfleet:hier:'):
            name = lab.split(':')[-1]
            h = next(a['path'] for a in m['artifacts'] if a['type'] == 'SCREEN_HIERARCHY')
            out = []; texts(json.load(open(f'{d}/{h}')), out)
            open(f'results/{run}/{name}.txt', 'w').write('\n'.join(dict.fromkeys(out)) + '\n')
            print(run, name, 'screenshot', shot, '->', len(out), 'strings', h, round(m['duration']), 'ms')
